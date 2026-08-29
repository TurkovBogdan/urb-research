# Class — `classDiagram`

For type structure: classes, interfaces, what inherits from what. Useful when describing a
design or an existing module's shape.

## A class

```mermaid
classDiagram
  class Animal {
    +String name
    +int age
    +eat() void
    +sleep() void
  }
```

A member is `<visibility><type> <name>` for a field and `<visibility><name>(args) <return>` for
a method — the type goes **first** for fields and **last** for methods.

The same members can be written one per line, outside any block. That form is easier to grow and
mixes freely with relationships:

```mermaid
classDiagram
  ServiceGateway <|-- TavilyGateway
  ServiceGateway <|-- XaiGateway
  ServiceGateway: +String SERVICE
  ServiceGateway: +balance() ConnectorBalance
  XaiGateway: +responses() dict
```

## Visibility

```mermaid
classDiagram
  class User {
    +String name
    -String password
    #int internalId
    ~String packageField
    +login() bool
    -hashPassword() String
  }
```

`+` public, `-` private, `#` protected, `~` package.

## Annotations

```mermaid
classDiagram
  class Serializable {
    <<interface>>
    +serialize() String
  }
  class Shape {
    <<abstract>>
    +area() double
  }
  class Status {
    <<enumeration>>
    ACTIVE
    INACTIVE
    PENDING
  }
```

An enum lists its values as bare members — no types, no visibility markers.

## Relationships

```mermaid
classDiagram
  A <|-- B : inheritance
  C *-- D : composition
  E o-- F : aggregation
  G --> H : association
  I ..> J : dependency
  K ..|> L : realization
```

Read them as: `<|--` "B is an A"; `*--` "D is part of C and dies with it"; `o--` "F belongs to E
but outlives it"; `-->` "G uses H"; `..>` "I depends on J"; `..|>` "K implements L".

The label after `:` is optional and usually earns its place:

```mermaid
classDiagram
  class Teacher {
    +String name
  }
  class Course {
    +String title
  }
  Teacher --> Course : teaches
```

Generics are written with tildes: `-List~Observer~ observers`.

## Worked example — the observer pattern

```mermaid
classDiagram
  class Subject {
    <<interface>>
    +attach(Observer) void
    +detach(Observer) void
    +notify() void
  }
  class Observer {
    <<interface>>
    +update() void
  }
  class EventEmitter {
    -List~Observer~ observers
    +attach(Observer) void
    +notify() void
  }
  class Logger {
    +update() void
  }
  Subject <|.. EventEmitter
  Observer <|.. Logger
  EventEmitter --> Observer
```

> Only list the members that carry the point. A class box reproduced field-for-field from the
> source is a worse version of the source — the diagram exists to show the relationships.
