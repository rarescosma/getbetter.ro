Title: 12 Factor Applications
Tags: Interview, Wiki

This is a summarized version of the well-established 12 factor applications concept from the DevOps world, sorted by importance. 

## Non-negociable

### 1. The codebase

> Use the source control, Luke.

The app should have a single codebase tracked in a revision control system. Many deploys are possible, but they should all originate from the same codebase.

## High Importance

### 2. Dependencies

> Explicitly declare and isolate dependencies.

Without this, the team will have a constant slow time-suck of confusion and frustration multiplied by the size and number of applications. 

### 3. Backing services

> Treat backing services as attached resources.

Reference backing services by a simple, cluster-wide endpoint. (like an URL, or a domain name)

The code shouldn't know the difference between a backing service hosted in a different data center, or SaaS, managed, etc.

### 4. Processes

> Execute the app as one or more stateless processes.

Try to keep the state (persistence layer) of your app completely defined by your databases and shared storage, and not by each individual running app instance. 

Stateless apps are more robust, easier to manage, incur fewer bugs and scale better.

### 5. Admin processes

> Run admin/management tasks as one-off processes.

Not sure about this one, it does not seem to have aged well.

## Medium

### 6. Config

> Store configuration in the environment.

Configuration should vary between different environments, but code shouldn't.

Ergo, try to store configuration data separate from the code and have the code read it at runtime.

### 7. Port binding

> Expose services via port binding.

As an extension to the "Backing services" principle, the app itself should also interface with the outside world via a simple URL. 

Different purposes should be mapped to different domain names (for example: authenticated, rate-limited public APIs vs. internal APIs)

### 8. Disposability

> Maximize robustness with fast startup and graceful shutdown.

New versions of the application should ideally launch right away and start to handle traffic. Also, there shouldn't be any mandatory "cleanup" tasks required after application shutdown.

## Low

### 9. Production / development parity

> Keep dev, staging and production environments as similar as possible.

This minimizes the risk of unexpected behaviour upon entering production. Virtualization usually helps.

### 10. Concurrency

> Scale out via the process model.

Specific needs should be handled by lots of little independent processes. This means each concerned can be scaled separately as needed.  

### 11. Logs

> Treat logs as event streams.

In production, logs should be captured as a stream of events and pushed into a real-time consolidated system for long-term archival and data-mining. 

## Conceptual

### 12. Build, release, run

> Strictly separate build and run stages.

Keep the "run" stage simple and bullet-proof. The "build" stage should do all the heavy lifting. 
