# Chat Coordinator 

What is the main event flow?

option 1: activation with user input
option 2: activation without user input

Activation event types:

- start generating a message to send
- send out the generated message

External events (methods)

- new message from user

## Very simple flow

- user sends us a message
- create event "generate a response"
- create event "send a response"

## Self activation flow

- generate an event
- someone generates next event