import argparse
import asyncio
import logging
import os
import random
import time
import platform
import cv2

from av import VideoFrame

from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
)
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder
from aiortc.contrib.signaling import ApprtcSignaling

ROOT = os.path.dirname(__file__)
PHOTO_PATH = os.path.join(ROOT, "photo.jpg")

import Motor
motor = Motor.Motor()

class VideoImageTrack(VideoStreamTrack):
    """
    A video stream track that returns a rotating image.
    """

    def __init__(self):
        super().__init__()  # don't forget this!
        self.img = cv2.imread(PHOTO_PATH, cv2.IMREAD_COLOR)

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        # rotate image
        rows, cols, _ = self.img.shape
        M = cv2.getRotationMatrix2D((cols / 2, rows / 2), int(pts * time_base * 45), 1)
        img = cv2.warpAffine(self.img, M, (cols, rows))

        # create video frame
        frame = VideoFrame.from_ndarray(img, format="bgr24")
        frame.pts = pts
        frame.time_base = time_base

        return frame

def channel_log(channel, t, message):
    print("channel(%s) %s %s" % (channel.label, t, message))

def channel_send(channel, message):
    channel_log(channel, ">", message)
    channel.send(message)

time_start = None

def current_stamp():
    global time_start

    if time_start is None:
        time_start = time.time()
        return 0
    else:
        return int((time.time() - time_start) * 1000000)

async def run(pc, player, recorder, signaling):
    def add_tracks():
        if player and player.audio:
            pc.addTrack(player.audio)

        if player and player.video:
            pc.addTrack(player.video)
        else:
            pc.addTrack(VideoImageTrack())

    @pc.on("track")
    def on_track(track):
        print("Track %s received" % track.kind)
        recorder.addTrack(track)

    # connect to websocket and join
    params = await signaling.connect()

    if params["is_initiator"] == "true":
        # send offer
        add_tracks()
        channel = pc.createDataChannel("chat")
        channel_log(channel, "-", "created by local party")

        async def send_pings():
            while True:
                channel_send(channel, "ping %d" % current_stamp())
                await asyncio.sleep(10)

        @channel.on("open")
        def on_open():
            asyncio.ensure_future(send_pings())

        @channel.on("message")
        def on_message(message):
            channel_log(channel, "<", message)

            if isinstance(message, str) and message.startswith("pong"):
                elapsed_ms = (current_stamp() - int(message[5:])) / 1000
                print(" RTT %.2f ms" % elapsed_ms)

        @channel.on("error")
        def on_error(message):
            print(" Error %s" % message)

        @channel.on('data')
        def data_handler(data):
            print(" Data %s" % data)

    await pc.setLocalDescription(await pc.createOffer())
    await signaling.send(pc.localDescription)

    # consume signaling
    while True:
        obj = await signaling.receive()

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)
            await recorder.start()

            if obj.type == "offer":
                # send answer
                add_tracks()
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)
        elif isinstance(obj, RTCIceCandidate):
            pc.addIceCandidate(obj)
        elif obj is None:
            print("Exiting")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AppRTC")
    parser.add_argument("room", nargs="?")
    parser.add_argument("--play-from", help="Read the media from a file and sent it."),
    parser.add_argument("--record-to", help="Write received media to a file."),
    parser.add_argument("--verbose", "-v", action="count")
    parser.add_argument("--server", help="https://your.appr.tc")
    args = parser.parse_args()

    if not args.room:
        args.room = "".join([random.choice("0123456789") for x in range(10)])

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    # create signaling and peer connection
    signaling = ApprtcSignaling(args.room)
    signaling._origin = args.server
    pc = RTCPeerConnection()

    # create media source
    if args.play_from:
        player = MediaPlayer(args.play_from)
    else:
        #player = None
        options = {"framerate": "10", "video_size": "320x240"}
        if platform.system() == "Darwin":
            player = MediaPlayer("default:none", format="avfoundation", options=options)
        else:
            player = MediaPlayer("/dev/video0", format="v4l2", options=options)

    # create media sink
    if args.record_to:
        recorder = MediaRecorder(args.record_to)
    else:
        recorder = MediaBlackhole()

    @pc.on("datachannel")
    def on_datachannel(remotechannel):
        channel_log(remotechannel, "-", "created by remote party")

        @remotechannel.on("message")
        def on_message(message):
            channel_log(remotechannel, "<<<", message)
            
            if (message == "w"):
                motor.ahead()
            elif (message == "s"):
                motor.rear()
            elif (message == "a"):
                motor.left()
            elif (message == "d"):
                motor.right()
            elif (message == "e"):
                motor.quit()

    # run event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            run(pc=pc, player=player, recorder=recorder, signaling=signaling)
        )
    except KeyboardInterrupt:
        pass
    finally:
        # cleanup
        loop.run_until_complete(recorder.stop())
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())
