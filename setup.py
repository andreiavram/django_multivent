from distutils.core import setup

setup(
    name='django_multivent',
    version='0.1',
    packages=['multivent', 'multivent.migrations'],
    url='',
    license='MIT',
    author='Andrei Avram',
    author_email='andrei.avram@gmail.com',
    description='The purpose of this project is to provide views that allow for displaying any event-type data in various formats (pdf / svg planner, timelines, calendars)'
)
