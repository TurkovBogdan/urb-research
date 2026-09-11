# Flowchart — `graph` / `flowchart`

The workhorse: pipelines, decision trees, architecture. `graph` and `flowchart` are
interchangeable openers.

## Direction

```mermaid
graph TD
  A[Start] --> B[Process] --> C[End]
```

`TD` top-down (default choice, `TB` is the same thing), `LR` left-right, `BT` bottom-top,
`RL` right-left.

> `LR` is the most common way to ruin a diagram here: five nodes with sentence-long labels laid
> out left-to-right measure 1399 px and are shown at 38% — a strip of grey ripple. Use `LR` for
> three or four short nodes and `TD` for everything else.

## Shapes

Twelve shapes, and the brackets around the label pick one:

```mermaid
graph LR
  A[Rectangle] --> B(Rounded)
  B --> C{Diamond}
  C --> D([Stadium])
  D --> E((Circle))
  E --> F[[Subroutine]]
  F --> G(((Double Circle)))
  G --> H{{Hexagon}}
  H --> I[(Database)]
  I --> J>Flag]
  J --> K[/Trapezoid\]
  K --> L[\Inverse Trap/]
```

In practice four carry meaning and the rest are noise: `[…]` a step, `{…}` a decision,
`([…])` a start/end, `[(…)]` a store. Use a shape to say something, not to vary the picture.

## Edges

```mermaid
graph TD
  A[Source] -->|solid| B[Target 1]
  A -.->|dotted| C[Target 2]
  A ==>|thick| D[Target 3]
```

Without an arrowhead: `---` solid, `-.-` dotted, `===` thick. Bidirectional: `<-->`, `<-.->`,
`<==>`.

Labels come in two forms — `-->|label|` and `-- label -->`:

```mermaid
flowchart TD
  A(Start) --> B{Is it sunny?}
  B -- Yes --> C[Go to the park]
  B -- No --> D[Stay indoors]
  C --> E[Finish]
  D --> E
```

Chaining and fan-out keep the source short:

```mermaid
graph LR
  A[Step 1] --> B[Step 2] --> C[Step 3] --> D[Step 4]
```

```mermaid
graph TD
  A[Input] & B[Config] --> C[Processor]
  C --> D[Output] & E[Log]
```

## Subgraphs

`subgraph id [Display label] … end` — the id is what edges point at, the bracketed label is what
the reader sees. `subgraph id ["Метка со словами"]` with quotes works too and is the safer form
for a label with spaces or punctuation. A subgraph may override the direction of its own
contents:

```mermaid
graph TD
  subgraph pipeline [Processing Pipeline]
    direction LR
    A[Input] --> B[Parse] --> C[Transform] --> D[Output]
  end
  E[Source] --> A
  D --> F[Sink]
```

Nesting works, and edges may cross a boundary from outside:

```mermaid
graph TD
  subgraph Cloud
    subgraph us-east [US East Region]
      A[Web Server] --> B[App Server]
    end
    subgraph us-west [US West Region]
      C[Web Server] --> D[App Server]
    end
  end
  E[Load Balancer] --> A
  E --> C
```

## Styling — sparingly

Colours are supplied by the app theme (see the main guide). When a distinction genuinely needs
colour, there are three ways:

```mermaid
graph TD
  A[Normal]:::default --> B[Highlighted]:::highlight --> C[Error]:::error
  classDef default fill:#f4f4f5,stroke:#a1a1aa
  classDef highlight fill:#fbbf24,stroke:#d97706
  classDef error fill:#ef4444,stroke:#dc2626
```

```mermaid
graph TD
  A[Default] --> B[Custom Colors] --> C[Another Custom]
  style B fill:#3b82f6,stroke:#1d4ed8,color:#ffffff
```

Both land in the rendered SVG. **`linkStyle` does not** — this renderer accepts the line without
complaint and ignores it, so edges cannot be coloured here. Carry the distinction on the nodes
(`:::class`) or in the edge label instead; a `linkStyle` block is dead weight that also reads to
the next author as if it worked.

## Worked example — a CI pipeline

```mermaid
graph TD
  subgraph ci [CI Pipeline]
    A[Push Code] --> B{Tests Pass?}
    B -->|Yes| C[Build Image]
    B -->|No| D[Fix & Retry]
    D -.-> A
  end
  C --> E([Deploy Staging])
  E --> F{QA Approved?}
  F -->|Yes| G((Production))
  F -->|No| D
```
