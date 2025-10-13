#!/usr/bin/env python3
"""
Probe common RTSP/MJPEG endpoints for an IP camera to find a working stream URL.

Usage:
  python tools\probe_camera_streams.py 192.168.22.254 [--user user] [--pass password] [--port 554]

The script will try several common paths and report which ones return a frame.
"""
import cv2
import time
import argparse


COMMON_RTSP_PATHS = [
    '/stream',
    '/live.sdp',
    '/h264',
    '/ch0_0.264',
    '/1',
    '/0',
    '/media.amp',
    '/onvif1',
    '/cam/realmonitor?channel=1&subtype=0',
    '/mpeg4',
    '/live',
]

COMMON_HTTP_PATHS = [
    '/video',
    '/videostream.cgi',
    '/cgi-bin/mjpg/video.cgi',
    '/axis-cgi/mjpg/video.cgi',
    '/cgi-bin/stream.mjpg',
    '/mjpeg.cgi',
    '/Streaming/channels/1/httpPreview',
    '/Streaming/Channels/101',
]


def try_url(url, timeout=2.0):
    try:
        cap = cv2.VideoCapture(url)
        # allow backend to initialize
        time.sleep(0.4)
        ok, frame = cap.read()
        cap.release()
        return ok
    except Exception:
        return False


def build_urls(ip, port=None, user=None, password=None):
    urls = []
    host = ip if port is None else f"{ip}:{port}"

    # RTSP candidates
    for p in COMMON_RTSP_PATHS:
        base = f"rtsp://{host}{p}"
        urls.append(base)
        if user:
            urls.append(f"rtsp://{user}:{password}@{host}{p}")

    # HTTP/MJPEG candidates
    for p in COMMON_HTTP_PATHS:
        base = f"http://{host}{p}"
        urls.append(base)
        if user:
            urls.append(f"http://{user}:{password}@{host}{p}")

    # Some cameras expose typical short paths
    urls.extend([
        f"rtsp://{host}",
        f"http://{host}",
    ])
    if user:
        urls.extend([
            f"rtsp://{user}:{password}@{host}",
            f"http://{user}:{password}@{host}",
        ])

    # De-duplicate while preserving order
    seen = set()
    uniq = []
    for u in urls:
        if u not in seen:
            uniq.append(u)
            seen.add(u)
    return uniq


def main():
    parser = argparse.ArgumentParser(description='Probe camera stream URLs')
    parser.add_argument('ip', help='IP address of the camera')
    parser.add_argument('--port', type=int, default=554, help='Port to try (default 554 for RTSP)')
    parser.add_argument('--user', help='Username for basic auth (optional)')
    parser.add_argument('--pass', dest='password', help='Password for basic auth (optional)')
    args = parser.parse_args()

    urls = build_urls(args.ip, port=args.port, user=args.user, password=args.password)

    print(f"Probing {len(urls)} candidate URLs (this may take a little while)...")
    success = []
    for u in urls:
        print(f"Trying: {u}", end=' -> ', flush=True)
        ok = try_url(u)
        print('OK' if ok else 'NO')
        if ok:
            success.append(u)

    print('\nDone. Working URLs:')
    if success:
        for s in success:
            print('  -', s)
    else:
        print('  (none found)')


if __name__ == '__main__':
    main()
