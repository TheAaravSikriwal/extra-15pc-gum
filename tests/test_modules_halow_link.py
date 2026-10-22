"""The ground station's end of the HaLow link in the sim: real datagrams on localhost, dropped
at the loss the model gives, and counted a second at a time."""

import asyncio
import socket

import pytest

from pcs14.flight.run import HalowLink


async def send(port: int, count: int, batch: int = 50):
    """`count` datagrams, a batch at a time with the loop let in between: sent all at once,
    they overflow the socket's buffer before the listener reads any, and the kernel drops
    them, not the model."""
    out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for k in range(count):
        out.sendto(b"mavlink %d" % k, ("127.0.0.1", port))
        if k % batch == batch - 1:
            await asyncio.sleep(0.002)
    out.close()


async def through(loss: float, count: int = 2000) -> HalowLink:
    clock = {"t": 10.2}
    link = HalowLink(0, loss=lambda: loss, now=lambda: clock["t"], distance=lambda: 4321.0)
    await link.start()
    await send(link.port, count)
    await asyncio.sleep(0.3)
    link.close()
    return link


@pytest.mark.parametrize(("loss", "share"), [(0.0, 1.0), (0.5, 0.5), (1.0, 0.0)])
def test_it_drops_what_the_model_says(loss, share):
    link = asyncio.run(through(loss))
    (bucket,) = link.seconds  # everything came in the same second of the sim
    assert bucket.t == 10 and bucket.distance_m == 4321.0
    assert bucket.sent == 2000
    assert bucket.delivered / bucket.sent == pytest.approx(share, abs=0.05)
