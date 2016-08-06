import subprocess
import logging

logger = logging.getLogger(__name__)

def call_and_log(*args, **kwargs):
    """Run process, gather output and write to log"""
    p = subprocess.Popen(*args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
    stdout, stderr = p.communicate()
    if len(stdout) > 0:
        logger.info(stdout.decode("utf-8").strip())
    if len(stderr) > 0:
        logger.error(stderr.decode("utf-8").strip())
    if p.returncode != 0:
        logger.error("{} returned {}".format(p.args, p.returncode))

def long_running(*args, **kwargs):
    """Run process redirecting stderr to stdout and write output to log"""
    p = subprocess.Popen(*args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, **kwargs)
    with p.stdout:
        for line in iter(p.stdout.readline, b''):
            logger.error(line.decode("utf-8").strip())

    p.wait()
    if p.returncode != 0:
        logger.error("{} returned {}".format(p.args, p.returncode))
