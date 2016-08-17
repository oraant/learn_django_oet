class BasicHandler:

    """Handle data like init,clear,show and reset."""

    def __init__(self):

        """Declare your basic data here."""

        self.orm = ''
        self.fields = []
        self.data = []

    def putin(self):

        """ put init data into your orm table """

        keys = []

        for i, v in enumerate(self.fields):
            tmp = '%s=row[%d]' % (v, i)
            keys.append(tmp)

        create = 'self.orm.objects.create(%s)' % ','.join(keys)

        for row in self.data:
            exec create

        print 'insert %d rows data into %s.' % (i+1,self.orm.__name__)

    def show(self):

        """ overwrite this method if your orm table don't have name column """

        rows = self.orm.objects.all()

        if len(rows) == 0:
            print "no rows here"
            return

        def f(x): print '  %s' % x.name

        map(f, rows)

    def clear(self):

        """ delete all datas from your orm table """

        self.orm.objects.all().delete()

    def reset(self):

        """ delete current datas and put original datas in your orm table """

        self.clear()
        self.putin()
