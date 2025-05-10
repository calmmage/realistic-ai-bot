# Todos

- [x] a - just split in the end 
- [x] b - streaming (technical - but still send in the end..)
- [ ] c - streaming + send as you go
- [x] d - 'reply safe / answer safe'

- [ ] add history - accumulate messages for user
  - [ ] improve - rotate out extra context on timeout
  - [ ] option 1: in-memory
  - [ ] option 2: mongodb
  - [ ] option 3: queue class? 
  - [ ] bonus: add and use mongodb vector storage for RAG

- [ ] split messages simple
  - [x] Just wire it - so that it at least works at all.. (None mode)
  - [x] simple
  - [x] simple improved
  - [ ] markdown
  - [ ] structured
- [ ] delay messages (e.g. send_out_messages) feature
  - [x] Just wire it - so that it at least works at all.. (None mode)

- [ ] split messages streaming
  - [ ] Just wire it - so that it at least works at all.. (None mode)

---

## Next main improvement idea:

- support the interaction where user writes to the chatbot also in multiple messages - potentially writing in the middle of next message without waiting for response to finish...
- [ ] idea 1: maintain a shared message -> response (chat) history and use it across processes
- [ ] idea 2: stop responding to a previous message (interrupt) when new one arrives
- [ ] automatically activate 'reply' mode when this happens - otherwise, use 'answer' by default

---

## more small todos

- [ ] for 'typing' status also add a delay without 'typing' - somehow...
- [x] add markdown / html formatting to responses
- [ ] wait for the user to finish sending the message
  - we can try to use multi-message mode for that
  - configure the ... somehow? 

---

## Settings

- [ ] Implement a web-app settings with slider (e.g. for 'delay between messages' variable
- [ ] Implement a basic 'settings' component for botspot, that gets a list of variables, setters, and gives user a nice menu / ui for setting them all (e.g. commands, ask_user_choice etc.)

---

## Next cool feature

random activations

How to implement?

- Idea 1: activate on a trigger schedule. Then random check + see if user wrote recently.
- Idea 2: Ask AI to generate when to try to activate next
  - Still sanity-check

---

## One more feature

"Think a little more" feature
-> after responding (or during?)

-> trigger the query / thinking mode once more
-> evaluate if the new thought is worth sharing
-> if not, just ignore it

---

## And one more

- emulate 'being offline' - be online in random time during the day
- (unique for each user)

---

## Make bot more human

- make responses proportional in length to original request

---

## Release

- [ ] deploy the bot
- [ ] add some way to limit money exposure
  - idea 1: custom anthorpic / openai key with limit on $
  - idea 2: what is my status on 'trial mode limits'? 

---

## Done

- [x] basic chat
- [x] media support
- [x] add main feature: splitting the ai response into parts
    - [x] add (randomized?) delay between messages
    - [x] add custom formatting instructions for system prompt - e.g. split formatting mode

- [x] add model selection command / menu
  - [x] use model for querying
  - [x] add a command - model picker (with ask_user_choice util)