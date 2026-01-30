.. Ari and Evo documentation master file, created by
   sphinx-quickstart on Tue Jan 13 15:25:43 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Ari & Evo Python API
====================

Welcome to the Ari & Evo Python API documentation. This library provides interfaces to control Ozobot's Ari and Evo robots.

There are two main ways to use this library:

*   **Synchronous API**: Designed for beginners or simple scripts. It uses blocking calls and hides the complexity of concurrency. See :ref:`sync_evo` for more details.
*   **Asynchronous API**: Recommended for advanced users and complex applications. It is built on Python's ``asyncio`` and allows for concurrency, cancellation, and advanced sensor monitoring. See :ref:`async_evo` for more details.
