# Access Log Api

## Design Principles
* Seperate API and data implementation
* Data log processor expects a generator which provides normalized and ordered (by time, mixed users) events stream.

## Unfulfilled Desired Requirements
Becuase of shortage of time I had to compromise on some guidelines which I think are important:
* Data loader should be able to absorb additional logs in efficient ways, handling overlaps with previous data. 
* My implemtation assumes too much about the format of the log. Should I had more time I would have designed the log parsers as "drivers" to handle different log fomats and handle parsing events errors instead of failing a complete log.
* I used sorting to order the events, this should have been optimized by insert sort implementation.
* ID - I used a compoud key of user-id+offset as the anchor ID. More useful would be global id. The offsets may change and compound keys are inconvenient. A global id can factor in additional infromation such as organization id and resource id for multiple clients support.
* The API response is overly verbose and has repeating elements. No excuses - only because of shortage of time.
* There is no MT protection.
* No API exception handling. Exceptions would produce HTTP errors when running a server like Flask, but it is not pretty.
* I don't know if it was expected - I didn't run a web server, I used an API in code in a similar manner as I would with Flask. In case this is required I can add it quickly.

## Data Blocks
The normalized log data should be ordered by timestamps and split up somehow to units which contain a complete list of events in a limited time window and limited number of users.
The reason for this guideline is so important in my opinion, is for practical reasons as well as performance reasons.
The units, which I call blocks can become: files, HDFS or S3 files or spark files and documents in nosql DB.
This implementation is based on an index of users, each index is linked to an ordered list of blocks with fixed size events. 
A block has 2 arrays: timestamps list for b-search search, and events list. This can be thought of as a key-value pairs. ts->event data.

