.. _sync_apidoc:

Ari synchronnous API reference
==============================

.. autoclass:: ozobot.ari.SyncAriHandle
	:members:
	:inherited-members:
	:exclude-members: connect

	.. overwrite connect because sphinx does not seem to handle contextlib.contextmanager correctly 

	.. automethod:: connect() -> typing.ContextManager[SyncAri]

.. autoclass:: ozobot.ari.SyncAri
	:members:
	:inherited-members:

.. autoclass:: ozobot.ari.api.sync.SyncAriVirtualMemory
	:members:
	:inherited-members:


Evo synchronnous API reference
==============================

.. autoclass:: ozobot.evo.SyncEvoHandle
	:members:
	:inherited-members:
	:exclude-members: connect

	.. overwrite connect because sphinx does not seem to handle contextlib.contextmanager correctly 

	.. automethod:: connect() -> typing.ContextManager[SyncEvo]

.. autoclass:: ozobot.evo.SyncEvo
	:members:
	:inherited-members:

.. autoclass:: ozobot.evo.api.sync.SyncEvoVirtualMemory
	:members:
	:inherited-members:

