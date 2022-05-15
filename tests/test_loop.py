from collections import deque
import asyncio
import pytest
import asynkit


class TestRotateReady:
    """
    Test that tasks, ready to execute, can be rotated in the ready queue
    using the rotate_ready() loop method
    """

    async def simple(self, arg):
        self.log.append(arg)

    def tasks(self, n=3):
        self.log = []
        self.tasks = [asyncio.create_task(self.simple(k)) for k in range(n)]
        return list(range(n))

    async def gather(self):
        await asyncio.gather(*self.tasks)
        return self.log

    def rotate(self, l, r):
        d = deque(l)
        d.rotate(r)
        return list(d)

    async def test_three_normal(self):
        log0 = self.tasks()
        assert await self.gather() == log0

    async def test_two_shift_one(self):
        log0 = self.tasks()
        asyncio.get_running_loop().rotate_ready(1)
        assert await self.gather() == self.rotate(log0, 1)

    @pytest.mark.parametrize("shift", [-3, -2, -1, 0, 1, 2, 3])
    async def test_five_multi(self, shift):
        log0 = self.tasks(5)
        asyncio.get_running_loop().rotate_ready(shift)
        assert await self.gather() == self.rotate(log0, shift)


class TestCallInsertReady:
    """
    Test that we can insert callbacks at given places in the runnable
    queue.  Compare the order of execution with a list that has been
    similarly inserted into via list.insert()
    """

    def add_insert(self, pos, label):
        def callback():
            self.log.append(label)

        asyncio.get_running_loop().call_insert(pos, callback)

    def prepare(self, n=3):
        self.log = []
        self.tasks = [asyncio.create_task(self.simple(k)) for k in range(n)]
        return list(range(n))

    @pytest.mark.parametrize("count", [1, 2, 6])
    async def test_normal(self, count):
        self.log = []
        expect = []
        perm = list(range(count))
        for i, pos in enumerate(perm):
            self.add_insert(pos, i)
            expect.insert(pos, i)
        await asyncio.sleep(0)
        assert self.log == expect

    @pytest.mark.parametrize("count", [2, 6])
    async def test_reverse(self, count):
        self.log = []
        expect = []
        perm = list(range(count))
        perm.reverse()
        for i, pos in enumerate(perm):
            self.add_insert(pos, i)
            expect.insert(pos, i)
        await asyncio.sleep(0)
        assert self.log == expect

    @pytest.mark.parametrize("count", [2, 6])
    async def test_cut(self, count):
        self.log = []
        expect = []
        perm = list(range(count))
        perm = perm[len(perm) // 2 :] + perm[: len(perm) // 2]
        perm.reverse()
        for i, pos in enumerate(perm):
            self.add_insert(pos, i)
            expect.insert(pos, i)
        await asyncio.sleep(0)
        assert self.log == expect


@pytest.mark.parametrize("count", [2, 6])
async def test_num_ready(count):
    for i in range(count):

        async def foo():
            pass

        asyncio.create_task(foo())

    assert asyncio.get_running_loop().num_ready() == count
    await asyncio.sleep(0)
    assert asyncio.get_running_loop().num_ready() == 0


async def test_sleep_insert():
    log = []
    for i in range(6):

        async def foo(n):
            log.append(n)

        asyncio.create_task(foo(i))

    assert asyncio.get_running_loop().num_ready() == 6
    await asynkit.sleep_insert(3)
    assert asyncio.get_running_loop().num_ready() == 3
    log.append("me")
    await asyncio.sleep(0)

    expect = list(range(6))
    expect.insert(3, "me")
    assert log == expect