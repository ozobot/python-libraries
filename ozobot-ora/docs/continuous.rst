Movement interpolation
----------------------

With standard movements, the robot stops after reaching individual points. To create a smooth movement, the robot can interpolate between points. 
This is done by specifying a radius around each point. The robot will then move in an arc specified radius until it reaches the next point. To do so,
the robot mostly not reach the intermediate point exactly, but will be close enough to the point to be considered as reached. 

.. image:: ./img/interpolation.svg
  :alt: comparison - motion through two points with and without interpolation enabled

  Comparing motion with and without interpolation


Default values for movement interpolation
=========================================

The default value for the interpolation radius is 10 mm. To change the interpolation radius, use the :py:meth:`set_default_radius` command.
