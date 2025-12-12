# Next
 - Require Python 3.13
 - Move to `python-libraries` repo, change structure to match repo conventions
 - ORA-341: add `replace` to datastructures
 - ORA-384: add `Input.wait` method to the simple api
 - ORA-596: initialize driver by context manager
 - ORA-572: manage current default speed on the Python side
 - ORA-593: remove unused cont parameter
 - Require Python 3.12

# 1.0.6
 - ORA-544: Fix analog output written instead of digital

# 1.0.5
 - Fix sphinx building
 - ORA-538: Use arrays to pass RPC arguments

# 1.0.4
 - ORA-468 OraWebDriver supports usage with device manger  
 - Fix sphinx building 

# 1.0.2
 - Fix async `write_outputs` to accept `int` as well as `float`
 - ORA-403 Generate API documentation on release
 - ORA-403 Remove motion interpolation from the documentation

# 1.0.1
 - Fix: `wait` function not working
 - Rename finger gripper state `CLOSE` to `CLOSED`
 - Temporarily remove `cont` keyword and references to movement interpolation
