<a name="prawvents"></a>
# PRAWvents, Events for PRAW (async PRAW)
A simple wrapper to write event-based bots with [async PRAW](https://asyncpraw.readthedocs.io/en/latest).

## Scope
You can register event handlers for everything that's based on the async PRAW [stream_generator](https://asyncpraw.readthedocs.io/en/latest/code_overview/other/util.html#asyncpraw.models.util.stream_generator)
Any other functionality is offered as-is, since these subclasses extend the main async PRAW [Reddit](https://asyncpraw.readthedocs.io/en/latest/code_overview/reddit_instance.html) instance.

Use the [original project](https://github.com/laundmo/prawvents) by [@laundmo](https://github.com/laundmo) for the 'sync' PRAW version.

# Quickstart

This is a simple bot that will print out the subreddit and the submission title for all posts in the subreddits AskReddit and pics, while skipping the existing posts in AskReddit.
This example assumes the presence of a [praw.ini](https://asyncpraw.readthedocs.io/en/latest/getting_started/configuration/prawini.html) in your working directory.
```py
import asyncio


async def main():
    from asyncpraw import reddit
    from prawvents import EventReddit

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
```

# Docs
<a name="prawvents.RedditEventDecorator"></a>
## RedditEventDecorator Objects

```python
class RedditEventDecorator()
```

Decorator class for event handlers.

<a name="prawvents.RedditEventDecorator.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(reddit: EventReddit, stream: RStream, err_handler: Callable)
```

Initialise RedditEventDecorator.

**Arguments**:

- `reddit` _EventReddit_ - The `EventReddit` instance
- `stream` _RStream_ - The stream to which the event responds.
- `err_handler` _Callable_ - A function that's called with the exception as a argument.

<a name="prawvents.RedditEventDecorator.__call__"></a>
#### \_\_call\_\_

```python
 | __call__(f: Callable) -> Callable
```

Set the event handler.

**Arguments**:

- `f` _Callable_ - The event handler function.


**Returns**:

- `Callable` - The function.

<a name="prawvents.EventReddit"></a>
## EventReddit Objects

```python
class EventReddit(asyncpraw.Reddit)
```

Main Reddit instance, subclass of [asyncpraw.Reddit](https://asyncpraw.readthedocs.io/en/latest/code_overview/reddit_instance.html).

**Arguments**:

- `asyncpraw` _asyncpraw.Reddit_ - Async PRAW Reddit superclass.

<a name="prawvents.EventReddit.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(*args, **kwargs)
```

Initialise EventReddit. All arguments are passed through to [asyncpraw.Reddit](https://asyncpraw.readthedocs.io/en/latest/code_overview/reddit_instance.html)

<a name="prawvents.EventReddit.register_event"></a>
#### register\_event

```python
 | register_event(stream: RStream, err_handler: Callable = None, **kwargs) -> RedditEventDecorator
```

Register an event, should generally be used as a decorator like this:

```py
@r.register_event(subreddit.stream.submissions, err_handler=handle_exception)
def event_handler(submission):
    pass
```

**Arguments**:

- `stream` _RStream_ - The stream to which the event responds.
- `err_handler` _Callable, optional_ - The error handler for this event. Defaults to None.


**Returns**:

- `RedditEventDecorator` - The decorator instance.

<a name="prawvents.EventReddit.handle_exception"></a>
#### handle\_exception

```python
 | handle_exception(f: RedditEventDecorator, e: Exception)
```

Handle an Exception happening in a function f

**Arguments**:

- `f` _RedditEventDecorator_ - The function which threw the exception.
- `e` _Exception_ - The exception which was thrown.


**Raises**:

- `e` - The Exception that was thrown.

<a name="prawvents.EventReddit.run_stream_till_none"></a>
#### run\_stream\_till\_none

```python
 | async run_stream_till_none(stream: RStream, funcs: Iterable[RedditEventDecorator]) -> None
```

Runs a stream until none is returned

**Arguments**:

- `stream` _RStream_ - The finalized stream to run.
- `funcs` _Iterable[RedditEventDecorator]_ - The functions which handle this stream.

<a name="prawvents.EventReddit.run_loop"></a>
#### run\_loop

```python
 | async run_loop(interweave=True) -> None
```

Run the event loop. If interweave is Truthy, events from multiple streams will be mixed to ensure a single high-traffic stream can't take up the entire event loop. This is highly 
recommended.

**Arguments**:

- `interweave` _bool, optional_ - Whether to interweave streams to ensure fair distribution. Defaults to True.