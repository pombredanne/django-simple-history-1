******************************************
Simple-history: History for Django Models
******************************************

django-simple-history is a tool to store state of DB objects on every create/update/delete. It has been tested to work in django 1.X (including 1.4 as of 08/30/2011).

**Install**

Download the tar.gz, extract it and run the following inside the directory:

.. code-block:: bash

    python setup.py install

**Basic usage**

Using this package is *really* simple; you just have to ``import HistoricalRecords`` and create an instance of it on every model you want to historically track.

Append the following line you your ``MIDDLEWARE_CLASSES``


.. code-block:: python

    MIDDLEWARE_CLASSES = (
      'simple_history.middleware.CurrentUserMiddleware',
      )

On your models you need to include the following line at the top:

.. code-block:: python

    from simple_history.models import HistoricalRecords


Then in your model class, include the following line:

.. code-block:: python

    history = HistoricalRecords()


Then from either the model class or from an instance, you can access ``history.all()`` which will give you either every history item of the class, or every history item of the specific instance.

**Example**

.. code-block:: python

    class Poll(models.Model):
        question = models.CharField(max_length = 200)
        pub_date = models.DateTimeField('date published')

        history = HistoricalRecords()

    class Choice(models.Model):
        poll = models.ForeignKey(Poll)
        choice = models.CharField(max_length=200)
        votes = models.IntegerField()

        history = HistoricalRecords()

.. code-block:: bash

    $ ./manage.py shell

.. code-block:: python

    In [2]: from poll.models import Poll, Choice

    In [3]: Poll.objects.all()
    Out[3]: []

    In [4]: import datetime

    In [5]: p = Poll(question="what's up?", pub_date=datetime.datetime.now())

    In [6]: p.save()

    In [7]: p
    Out[7]: <Poll: Poll object>

    In [9]: p.history.all()
    Out[9]: [<HistoricalPoll: Poll object as of 2010-10-25 18:03:29.855689>]

    In [10]: p.pub_date = datetime.datetime(2007,4,1,0,0)

    In [11]: p.save()

    In [13]: p.history.all()
    Out[13]: [<HistoricalPoll: Poll object as of 2010-10-25 18:04:13.814128>, <HistoricalPoll: Poll object as of 2010-10-25 18:03:29.855689>]

    In [14]: p.choice_set.create(choice='Not Much', votes=0)
    Out[14]: <Choice: Choice object>

    In [15]: p.choice_set.create(choice='The sky', votes=0)
    Out[15]: <Choice: Choice object>

    In [16]: c = p.choice_set.create(choice='Just hacking again', votes=0)

    In [17]: c.poll
    Out[17]: <Poll: Poll object>

    In [19]: c.history.all()
    Out[19]: [<HistoricalChoice: Choice object as of 2010-10-25 18:05:30.160595>]

    In [20]: Choice.history
    Out[20]: <simple_history.manager.HistoryManager object at 0x1cc4290>

    In [21]: Choice.history.all()
    Out[21]: [<HistoricalChoice: Choice object as of 2010-10-25 18:05:30.160595>, <HistoricalChoice: Choice object as of 2010-10-25 18:05:12.183340>, <HistoricalChoice: Choice object as of 2010-10-25 18:04:59.047351>]

**Copyright and license**

Copyright (c) 2012-2013 Pivotal Energy Solutions.  All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this work except in compliance with the License.
You may obtain a copy of the License in the LICENSE file, or at:

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
