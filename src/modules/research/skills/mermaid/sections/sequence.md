# Sequence — `sequenceDiagram`

For protocols and call flows: who talks to whom, in what order. The best fit for describing an
integration, an auth handshake or a request path.

## Participants

```mermaid
sequenceDiagram
  Alice->>Bob: Hello Bob!
  Bob-->>Alice: Hi Alice!
```

Declaring participants up front fixes their left-to-right order and lets you use short ids with
readable labels — this is also how you get a name with spaces, since ids cannot contain any:

```mermaid
sequenceDiagram
  participant A as Alice
  participant B as Bob
  participant C as Charlie
  A->>B: Hello
  B->>C: Forward
  C-->>A: Reply
```

`actor` draws a stick figure instead of a box — use it for the human at the edge of the flow:

```mermaid
sequenceDiagram
  actor U as User
  participant S as System
  participant DB as Database
  U->>S: Click button
  S->>DB: Query
  DB-->>S: Results
  S-->>U: Display
```

## Arrows

```mermaid
sequenceDiagram
  A->>B: Solid arrow (sync)
  B-->>A: Dashed arrow (return)
  A-)B: Open arrow (async)
  B--)A: Open dashed arrow
```

Convention worth keeping: solid `->>` for a call, dashed `-->>` for its answer. A reader picks
up the request/response rhythm from the line style alone.

## Activation and self-calls

`+` after the sender activates the receiver, `-` deactivates it — the lifeline grows a box for
the duration of the work:

```mermaid
sequenceDiagram
  participant C as Client
  participant S as Server
  C->>+S: Request
  S->>+S: Process
  S->>-S: Done
  S-->>-C: Response
```

The same participant on both sides is a self-message, drawn as a loop arrow:

```mermaid
sequenceDiagram
  participant S as Server
  S->>S: Internal process
  S->>S: Validate
```

## Control blocks

`loop` — repetition:

```mermaid
sequenceDiagram
  participant C as Client
  participant S as Server
  C->>S: Connect
  loop Every 30s
    C->>S: Heartbeat
    S-->>C: Ack
  end
  C->>S: Disconnect
```

`alt` / `else` — branches, as many `else` arms as needed:

```mermaid
sequenceDiagram
  participant C as Client
  participant S as Server
  C->>S: Login
  alt Valid credentials
    S-->>C: 200 OK
  else Invalid
    S-->>C: 401 Unauthorized
  else Account locked
    S-->>C: 403 Forbidden
  end
```

`opt` — a branch that may simply not happen; `par` / `and` — work that happens at the same time;
`critical` — a section that must not be interrupted:

```mermaid
sequenceDiagram
  participant C as Client
  participant A as AuthService
  participant U as UserService
  participant O as OrderService
  C->>A: Authenticate
  par Fetch user data
    A->>U: Get profile
  and Fetch orders
    A->>O: Get orders
  end
  A-->>C: Combined response
```

```mermaid
sequenceDiagram
  participant A as App
  participant DB as Database
  A->>DB: BEGIN
  critical Transaction
    A->>DB: UPDATE accounts
    A->>DB: INSERT log
  end
  A->>DB: COMMIT
```

## Notes

```mermaid
sequenceDiagram
  participant A as Alice
  participant B as Bob
  Note left of A: Alice prepares
  A->>B: Hello
  Note right of B: Bob thinks
  B-->>A: Reply
  Note over A,B: Conversation complete
```

`Note over X,Y:` spans two lifelines — the right way to comment on an interaction rather than on
a participant.

## Worked example — OAuth 2.0

```mermaid
sequenceDiagram
  actor U as User
  participant App as Client App
  participant Auth as Auth Server
  participant API as Resource API
  U->>App: Click Login
  App->>Auth: Authorization request
  Auth->>U: Login page
  U->>Auth: Credentials
  Auth-->>App: Authorization code
  App->>Auth: Exchange code for token
  Auth-->>App: Access token
  App->>API: Request + token
  API-->>App: Protected resource
  App-->>U: Display data
```

> A sequence diagram grows **down**, so length is cheap and width is not. Five participants is
> already a lot; past that, split the flow or collapse a group into one participant.
