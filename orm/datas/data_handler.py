class BaseHandler:

    def __init__(self):
        ''' declare your baseic datas '''
        self.orm = ''
        self.fields = []
        self.datas = []

    def putin(self):
        ''' put init datas into your orm table '''
        keylist = []
        for i,v in enumerate(self.fields):
            tmp = '%s=data[%d]' % (v,i)
            keylist.append(tmp)
        create = 'self.orm.objects.create(%s)' % ','.join(keylist)

        for data in self.datas:
            exec(create)

    def show(self):
        ''' overwrite this method if your orm table don't have name column '''
        rows = self.orm.objects.all()
        if len(rows) == 0:
            print "no rows here"
        def f(x):print '  %s' % x.name
        map(f,rows)

    def clear(self):
        ''' delete all datas from your orm table '''
        self.orm.objects.all().delete()

    def reset(self):
        ''' delete current datas and put original datas in your orm table '''
        self.clear()
        self.putin()
