from handler import BasicHandler


class Handler(BasicHandler):

    """Handle data with PTOra11gR2."""

    def __init__(self):

        from mirror.models import PTOra11gR2
        self.orm = PTOra11gR2

        self.fields = [
            'name','enable','desc','period',
            'pull',
            'create','drop','insert','delete'
        ]

        self.data = [
            (

                'test_v$database', 'True', '-', '10',
        
                '''select dbid,name,open_mode,log_mode from v$database''',
        
                ''' create table IF NOT EXISTS <TABLE_NAME>(
                        dbid int,
                        name varchar(30),
                        open_mode varchar(20),
                        log_mode varchar(20))
                    ENGINE = MEMORY ''',
        
                ''' drop table <TABLE_NAME> ''',
        
                ''' insert into <TABLE_NAME>
                    (dbid,name,open_mode,log_mode)
                    values (%s,%s,%s,%s) ''',
        
                ''' delete from <TABLE_NAME> '''

            ), (

                'test_v$sysstat', 'True', '-', '10',
        
                ''' select statistic#,name,class,value,stat_id
                    from v$sysstat
                    where name like '%DB time%' ''',
        
                ''' create table IF NOT EXISTS <TABLE_NAME>(
                        statistic bigint,
                        name varchar(64),
                        class bigint,
                        value bigint,
                        stat_id bigint)
                    ENGINE = MEMORY ''',
        
                ''' drop table <TABLE_NAME> ''',
        
                ''' insert into <TABLE_NAME>
                    (statistic,name,class,value,stat_id)
                    values (%s,%s,%s,%s,%s) ''',
        
                ''' delete from <TABLE_NAME> ''',

            )
        ]
