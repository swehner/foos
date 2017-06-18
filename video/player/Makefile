ILCLIENTDIR=/opt/vc/src/hello_pi/libs/ilclient
VGFONTDIR=/opt/vc/src/hello_pi/libs/vgfont

define DEP_ERROR_STRING
Can't find ilblient library - to build dependencies run:
    pushd /opt/vc/src/hello_pi; ./rebuild.sh; popd

endef

ifeq ("$(wildcard $(ILCLIENTDIR)/libilclient.*)","")
    $(error $(DEP_ERROR_STRING))
endif

CFLAGS+=-DSTANDALONE -D__STDC_CONSTANT_MACROS -D__STDC_LIMIT_MACROS -DTARGET_POSIX -D_LINUX -fPIC -DPIC -D_REENTRANT -D_LARGEFILE64_SOURCE -D_FILE_OFFSET_BITS=64 -U_FORTIFY_SOURCE -Wall -g3 -DHAVE_LIBOPENMAX=2 -DOMX -DOMX_SKIP64BIT -ftree-vectorize -pipe -DUSE_EXTERNAL_OMX -DHAVE_LIBBCM_HOST -DUSE_EXTERNAL_LIBBCM_HOST -DUSE_VCHIQ_ARM -Wno-psabi

LDFLAGS+=-L$(SDKSTAGE)/opt/vc/lib/ -lGLESv2 -lEGL -lopenmaxil -lbcm_host -lvcos -lvchiq_arm -lpthread -lrt -lm -L$(ILCLIENTDIR) -L$(VGFONTDIR)

INCLUDES+=-I$(SDKSTAGE)/opt/vc/include/ -I$(SDKSTAGE)/opt/vc/include/interface/vcos/pthreads -I$(SDKSTAGE)/opt/vc/include/interface/vmcs_host/linux -I./ -I$(ILCLIENTDIR) -I$(VGFONTDIR)

%.o: %.c
	@rm -f $@ 
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@ -Wno-deprecated-declarations

player: video.o
	$(CC) $(CFLAGS) $(LDFLAGS) -o player video.o -lilclient
