import collections
import inspect
from functools import partial
from typing import Any, Callable, Generator, Iterable, AsyncGenerator

import asyncpraw
from asyncpraw.models.util import stream_generator

RStream = stream_generator


class RedditEventDecorator:
    """Decorator class for event handlers.
    """

    def __init__(self, reddit: 'EventReddit', stream: RStream, err_handler: Callable):
        """Initialise RedditEventDecorator.

        Args:
            reddit (EventReddit): The `EventReddit` instance
            stream (RStream): The stream to which the event responds.
            err_handler (Callable): A function that's called with the exception as a argument.
        """
        self.err_handler = err_handler
        self.reddit = reddit
        self.stream = stream

    def __call__(self, f: Callable) -> Callable:
        """Set the event handler. 

        Args:
            f (Callable): The event handler function.

        Returns:
            Callable: The function.
        """
        self.reddit.streams[self.stream].append(f)
        f.stream = self
        return f


class EventReddit(asyncpraw.Reddit):
    """Main Reddit instance, subclass of [asyncpraw.Reddit](https://asyncpraw.readthedocs.io/en/latest/code_overview/reddit_instance.html).

    Args:
        asyncpraw (asyncpraw.Reddit): Async PRAW Reddit superclass.
    """

    def __init__(self, *args, **kwargs):
        """Initialise EventReddit. All arguments are passed through to [asyncpraw.Reddit](https://asyncpraw.readthedocs.io/en/latest/code_overview/reddit_instance.html)
        """
        super().__init__(*args, **kwargs)
        self.streams = collections.defaultdict(list)

    async def _every_second_generator(self, generator: AsyncGenerator) -> AsyncGenerator[Any, None]:
        """Return None in between original generator 

        Args:
            generator (Generator): The original generator

        Yields:
            Generator[Any, None, None]: The new generator which will add a None after each element of the original.
        """
        async for v in generator:
            yield v
            yield None

    def register_event(self, stream: RStream, err_handler: Callable = None, **kwargs) -> RedditEventDecorator:
        """Register an event, should generally be used as a decorator like this:
        ```py
        @r.register_event(subreddit.stream.submissions, err_handler=handle_exception)
        def event_handler(submission):
            pass
        ```

        Args:
            stream (RStream): The stream to which the event responds. 
            err_handler (Callable, optional): The error handler for this event. Defaults to None.

        Returns:
            RedditEventDecorator: The decorator instance.
        """
        stream = partial(stream, pause_after=-1, **kwargs)
        return RedditEventDecorator(self, stream, err_handler)

    def handle_exception(self, f: RedditEventDecorator, e: Exception):
        """Handle an Exception happening in a function f

        Args:
            f (RedditEventDecorator): The function which threw the exception.
            e (Exception): The exception which was thrown.

        Raises:
            e: The Exception that was thrown.
        """
        if f.stream.err_handler:
            f.stream.err_handler(e)
        else:
            raise e

    async def run_stream_till_none(self, stream: RStream, funcs: Iterable[RedditEventDecorator]) -> None:
        """Runs a stream until none is returned

        Args:
            stream (RStream): The finalized stream to run.
            funcs (Iterable[Callable]): The functions which handle this stream.
        """
        async for item in stream:
            if item is None:
                return
            for f in funcs:
                try:
                    if inspect.iscoroutinefunction(f):
                        await f(item)
                    else:
                        f(item)
                except Exception as e:
                    self.handle_exception(f, e)

    async def run_loop(self, interweave=True) -> None:
        """Run the event loop. If interweave is Truthy, events from multiple streams will be mixed to ensure a single high-traffic stream can't take up the entire event loop. This is highly recommended.

        Args:
            interweave (bool, optional): Whether to interweave streams to ensure fair distribution. Defaults to True.
        """
        streams = {self._every_second_generator(s()) if interweave else s(): funcs for s, funcs in self.streams.items()}
        while True:
            for stream, funcs in streams.items():
                await self.run_stream_till_none(stream, funcs)


if __name__ == "__main__":
    import asyncio


    async def main():
        from asyncpraw import reddit

        r = None
        try:
            r = EventReddit(
                user_agent=f"ExampleBot for prawvents version (0.0.1) by /u/laundmo")  # change the description and username!

            sub1 = await r.subreddit("AskReddit")
            sub2 = await r.subreddit("pics")

            def handle_exception(e):  # very dumb exception handler
                print(e)

            @r.register_event(sub1.stream.submissions, err_handler=handle_exception, skip_existing=True)
            @r.register_event(sub2.stream.submissions, err_handler=handle_exception)
            def handle(submission: reddit.Submission):
                print(submission.subreddit, submission.title)

            await r.run_loop()
        finally:
            if r:
                await r.close()


    asyncio.run(main())
