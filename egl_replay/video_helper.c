/*
Copyright (c) 2012, Broadcom Europe Ltd
Copyright (c) 2012, OtherCrashOverride
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the copyright holder nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

// Video decode demo using OpenMAX IL though the ilcient helper librar
#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "bcm_host.h"
#include "ilclient.h"

#include <pthread.h>

#include "GLES/gl.h"
#include "EGL/egl.h"
#include "EGL/eglext.h"

#define LOG printf

static OMX_BUFFERHEADERTYPE* eglBuffer = NULL;
static COMPONENT_T* egl_render = NULL;
static void* eglImage = 0;
static char filename[1024]; //"/opt/vc/src/hello_pi/hello_video/test.h264";
typedef void (*video_status_callback)();
static video_status_callback stop_callback=NULL;
static video_status_callback start_callback=NULL;

void init_video();

int init_textures(EGLDisplay display, EGLContext context, int width, int height, GLuint *out_tex) {
  GLuint tex;
  glGenTextures(1, &tex);
  
  glBindTexture(GL_TEXTURE_2D, tex);
  glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
	       GL_RGBA, GL_UNSIGNED_BYTE, NULL);
  
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
  

  /* Create EGL Image */
  eglImage = eglCreateImageKHR(display,
			       context,
			       EGL_GL_TEXTURE_2D_KHR,
			       (EGLClientBuffer)tex,
			       0);
  
  if (eglImage == EGL_NO_IMAGE_KHR) {
    LOG("eglCreateImageKHR failed.\n");
    return -1;
  }
  *out_tex = tex;

  init_video();
  return 0;
}

void fill_buffer_done(void* data, COMPONENT_T* comp) {
  if (OMX_FillThisBuffer(ilclient_get_handle(egl_render), eglBuffer) != OMX_ErrorNone) {
    LOG("OMX_FillThisBuffer failed in callback\n");
  }
}

// Modified function prototype to work with pthreads
void *video_decode_test(void* arg) {
  void* eglImage = arg;
  
  if (eglImage == 0){
    LOG("eglImage is null.\n");
    exit(1);
  }

  OMX_VIDEO_PARAM_PORTFORMATTYPE format;
  OMX_TIME_CONFIG_CLOCKSTATETYPE cstate;
  COMPONENT_T *video_decode = NULL, *video_scheduler = NULL, *clock = NULL;
  COMPONENT_T *list[5];
  TUNNEL_T tunnel[4];
  ILCLIENT_T *client;
  FILE *in;
  int status = 0;
  unsigned int data_len = 0;
  memset(list, 0, sizeof(list));
  memset(tunnel, 0, sizeof(tunnel));
  

  if ((client = ilclient_init()) == NULL) {
    return (void *)-3;
  }

  if (OMX_Init() != OMX_ErrorNone) {
    ilclient_destroy(client);
    return (void *)-4;
  }

  LOG("* setting up components\n");

  // callback
  ilclient_set_fill_buffer_done_callback(client, fill_buffer_done, 0);
   
  // create video_decode
  if (ilclient_create_component(client, &video_decode, "video_decode", ILCLIENT_DISABLE_ALL_PORTS | ILCLIENT_ENABLE_INPUT_BUFFERS) != 0)
    status = -14;
  
  list[0] = video_decode;
  
  // create egl_render
  if (status == 0 && ilclient_create_component(client, &egl_render, "egl_render", ILCLIENT_DISABLE_ALL_PORTS | ILCLIENT_ENABLE_OUTPUT_BUFFERS) != 0)
    status = -14;
  
  list[1] = egl_render;

  // create clock
  if (status == 0 && ilclient_create_component(client, &clock, "clock", ILCLIENT_DISABLE_ALL_PORTS) != 0)
    status = -14;
  
  list[2] = clock;
     
  // create video_scheduler
  if(status == 0 && ilclient_create_component(client, &video_scheduler, "video_scheduler", ILCLIENT_DISABLE_ALL_PORTS) != 0)
    status = -14;
  list[3] = video_scheduler;
  
  LOG("* setting up tunnel\n");

  set_tunnel(tunnel, video_decode, 131, video_scheduler, 10);
  set_tunnel(tunnel+1, video_scheduler, 11, egl_render, 220);
  set_tunnel(tunnel+2, clock, 80, video_scheduler, 12);
  

  // setup clock tunnel first
  if(status == 0 && ilclient_setup_tunnel(tunnel+2, 0, 0) != 0)
    status = -15;
  else
    ilclient_change_component_state(clock, OMX_StateExecuting);

  if(status == 0)
    ilclient_change_component_state(video_decode, OMX_StateIdle);

  memset(&format, 0, sizeof(OMX_VIDEO_PARAM_PORTFORMATTYPE));
  format.nSize = sizeof(OMX_VIDEO_PARAM_PORTFORMATTYPE);
  format.nVersion.nVersion = OMX_VERSION;
  format.nPortIndex = 130;
  format.eCompressionFormat = OMX_VIDEO_CodingAVC;
  // set framerate to 25 - if not it seems to use 30 as default
  format.xFramerate = 25 << 16;

  while (1) {
    if (strlen(filename) == 0) {
      usleep(100000);
      continue;
    }
    
    if (strcmp(filename, "quit")==0) {
      break;
    }
    LOG("playing: %s\n", filename);

    if ((in = fopen(filename, "rb")) == NULL) {
      LOG("No such file %s\n", filename);
      filename[0]='\0';
      continue;
    }
    filename[0]='\0';
    
    memset(&cstate, 0, sizeof(cstate));
    cstate.nSize = sizeof(cstate);
    cstate.nVersion.nVersion = OMX_VERSION;
    cstate.eState = OMX_TIME_ClockStateWaitingForStartTime;
    cstate.nWaitMask = 1;
    if(clock != NULL && OMX_SetParameter(ILC_GET_HANDLE(clock), OMX_IndexConfigTimeClockState, &cstate) != OMX_ErrorNone)
      status = -13;

    
    if(status == 0 &&
       OMX_SetParameter(ILC_GET_HANDLE(video_decode), OMX_IndexParamVideoPortFormat, &format) == OMX_ErrorNone &&
       ilclient_enable_port_buffers(video_decode, 130, NULL, NULL, NULL) == 0) {
      OMX_BUFFERHEADERTYPE *buf;
      int port_settings_changed = 0;
      int first_packet = 1;

      LOG("* executing decoder\n");

      ilclient_change_component_state(video_decode, OMX_StateExecuting);

      while((buf = ilclient_get_input_buffer(video_decode, 130, 1)) != NULL) {
	// feed data and wait until we get port settings changed
	unsigned char *dest = buf->pBuffer;
	
	data_len += fread(dest, 1, buf->nAllocLen-data_len, in);

	if (port_settings_changed == 0 &&
            ((data_len > 0 && ilclient_remove_event(video_decode, OMX_EventPortSettingsChanged, 131, 0, 0, 1) == 0) ||
             (data_len == 0 && ilclient_wait_for_event(video_decode, OMX_EventPortSettingsChanged, 131, 0, 0, 1,
                                                       ILCLIENT_EVENT_ERROR | ILCLIENT_PARAMETER_CHANGED, 10000) == 0))) {
	  LOG("* port settings changed\n");

	  port_settings_changed = 1;

	  if (ilclient_setup_tunnel(tunnel, 0, 0) != 0) {
	    status = -7;
	    break;
	  }

	  LOG("* executing scheduler\n");
	  ilclient_change_component_state(video_scheduler, OMX_StateExecuting);

	  LOG("* egl tunnel\n");

	  // now setup tunnel to egl_render
	  if(ilclient_setup_tunnel(tunnel+1, 0, 1000) != 0) {
	    status = -12;
	    break;
	  }

	  LOG("* egl idle\n");
	  // Set egl_render to idle
	  ilclient_change_component_state(egl_render, OMX_StateIdle);
	  
	  // Enable the output port and tell egl_render to use the texture as a buffer
	  //ilclient_enable_port(egl_render, 221); THIS BLOCKS SO CAN'T BE USED
	  if (OMX_SendCommand(ILC_GET_HANDLE(egl_render), OMX_CommandPortEnable, 221, NULL) != OMX_ErrorNone) {
	    LOG("OMX_CommandPortEnable failed.\n");
	    exit(1);
	  }

	  //TODO: Only do this the first time!
	  if (OMX_UseEGLImage(ILC_GET_HANDLE(egl_render), &eglBuffer, 221, NULL, eglImage) != OMX_ErrorNone) {
	    LOG("OMX_UseEGLImage failed.\n");
	    //exit(1);
	  }

	  LOG("* egl exec\n");

	  if (start_callback!=NULL) {
	    LOG("Calling start callback %p\n", start_callback);
	    start_callback();
	  }

	  // Set egl_render to executing
	  ilclient_change_component_state(egl_render, OMX_StateExecuting);

	  // Request egl_render to write data to the texture buffer
	  if(OMX_FillThisBuffer(ILC_GET_HANDLE(egl_render), eglBuffer) != OMX_ErrorNone) {
	    LOG("OMX_FillThisBuffer failed.\n");
	    exit(1);
	  }
	}
	if(!data_len)
	  break;

	buf->nFilledLen = data_len;
	data_len = 0;

	buf->nOffset = 0;
	if (first_packet) {
	  buf->nFlags = OMX_BUFFERFLAG_STARTTIME;
	  first_packet = 0;
	}
	else {
	  buf->nFlags = OMX_BUFFERFLAG_TIME_UNKNOWN;
	}
	
	//LOG("* empty buffer in loop\n");
	
	if(OMX_EmptyThisBuffer(ILC_GET_HANDLE(video_decode), buf) != OMX_ErrorNone) {
	  status = -6;
	  break;
	}
      }
      
      LOG("* end of loop\n");
      
      buf->nFilledLen = 0;
      buf->nFlags = OMX_BUFFERFLAG_TIME_UNKNOWN | OMX_BUFFERFLAG_EOS;
      
      LOG("* empty buffer\n");
      if(OMX_EmptyThisBuffer(ILC_GET_HANDLE(video_decode), buf) != OMX_ErrorNone) {
	status = -20;
	LOG("* error emptying last buffer\n");
      }

      LOG("* wait for eos\n");
      // wait for EOS from scheduler
      ilclient_wait_for_event(video_scheduler, OMX_EventBufferFlag, 11, 0, OMX_BUFFERFLAG_EOS, 0,
			      ILCLIENT_BUFFER_FLAG_EOS, 3000);
      
      ilclient_remove_event(video_scheduler, OMX_EventBufferFlag, 11, 0, OMX_BUFFERFLAG_EOS, 1);      
      /// end added

      // need to flush the renderer to allow video_decode to disable its input port
      LOG("* flush tunnels\n");
      ilclient_flush_tunnels(tunnel, 0);
      
      LOG("* disable port buffers\n");
      ilclient_disable_port_buffers(video_decode, 130, NULL, NULL, NULL);

      LOG("Stopping clock\n");
      memset(&cstate, 0, sizeof(cstate));
      cstate.nSize = sizeof(cstate);
      cstate.nVersion.nVersion = OMX_VERSION;
      cstate.eState = OMX_TIME_ClockStateStopped;
      cstate.nWaitMask = 1;
      if(clock != NULL && OMX_SetParameter(ILC_GET_HANDLE(clock), OMX_IndexConfigTimeClockState, &cstate) != OMX_ErrorNone) {
	LOG("ERROR Stopping clock\n");
	status = -13;
	
      }

      LOG("Close file\n");
      fclose(in);
      if (stop_callback!=NULL) {
	LOG("Calling stop callback %p\n", stop_callback);
	stop_callback();
      }
      LOG("After callback\n");
    }

  }
   

  LOG("CLosing tunnels 0\n");
  ilclient_disable_tunnel(tunnel);
  LOG("CLosing tunnels 1\n");
  ilclient_disable_tunnel(tunnel+1);
  LOG("CLosing tunnels 2\n");
  ilclient_disable_tunnel(tunnel+2);
  LOG("teardown tunnels\n");
  ilclient_teardown_tunnels(tunnel);

  LOG("set all idle\n");
  ilclient_state_transition(list, OMX_StateIdle);
  LOG("set all loaded\n");
  //ilclient_state_transition(list, OMX_StateLoaded);

  LOG("cleanup components\n");
  ilclient_cleanup_components(list);
  LOG("video finished\n");
  OMX_Deinit();

  ilclient_destroy(client);

  return (void *)status;
}


void run_video(char* f, video_status_callback startcb, video_status_callback stopcb) {
  LOG("Setting filename to %s\n", f);
  strncpy(filename, f, sizeof(filename));
  stop_callback = stopcb;
  start_callback = startcb;
}


void init_video() {
  pthread_t thread1;
  pthread_create(&thread1, NULL, video_decode_test, eglImage);
  pthread_setname_np(thread1, "videohelper");
}
