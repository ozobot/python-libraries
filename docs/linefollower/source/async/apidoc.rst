.. _async_apidoc:

Ari API reference
===================

.. autoclass:: ozobot.ari.AriHandle
	:members:
	:inherited-members:
	:exclude-members: connect

	.. overwrite connect because sphinx does not seem to handle contextlib.asynccontextmanager correctly 

	.. automethod:: connect() -> typing.AsyncContextManager[Ari]	

.. autoclass:: ozobot.ari.Ari
	:members:
	:inherited-members:

.. autoclass:: ozobot.ari.api.core.AriVirtualMemory
	:members:
	:inherited-members:


Evo API reference
=================

.. autoclass:: ozobot.evo.EvoHandle
	:members:
	:inherited-members:
	:exclude-members: connect

	.. overwrite connect because sphinx does not seem to handle contextlib.asynccontextmanager correctly 

	.. automethod:: connect() -> typing.AsyncContextManager[Evo]

.. autoclass:: ozobot.evo.Evo
	:members:
	:inherited-members:

.. autoclass:: ozobot.evo.api.core.EvoVirtualMemory
	:members:
	:inherited-members:

