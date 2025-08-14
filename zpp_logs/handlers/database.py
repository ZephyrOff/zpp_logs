from .base import BaseHandler
from sqlalchemy import create_engine, Column, Integer, String, DateTime, MetaData, Table, func
import os
import importlib

class DatabaseHandler(BaseHandler):
    def __init__(self, level, formatter, filters=None, connector=None, columns=None, ops='>=', async_mode=False, model=None):
        super().__init__(level=level, formatter=formatter, filters=filters, ops=ops, async_mode=async_mode)
        
        self.engine = self._create_engine(connector)
        self.model = model
        
        if self.model:
            if isinstance(self.model, str):
                module_name, class_name = self.model.rsplit('.', 1)
                module = importlib.import_module(module_name)
                self.model = getattr(module, class_name)
            
            self.log_table = self.model.__table__
            self.table_name = self.log_table.name
            self.log_table.create(self.engine, checkfirst=True)
            
            if columns is None:
                self.columns_mapping = {}
                if hasattr(self.model, 'timestamp'): self.columns_mapping['timestamp'] = 'timestamp'
                if hasattr(self.model, 'level'): self.columns_mapping['level'] = 'levelname'
                if hasattr(self.model, 'message'): self.columns_mapping['message'] = 'msg'
                if hasattr(self.model, 'logger_name'): self.columns_mapping['logger_name'] = 'name'
                if hasattr(self.model, 'user_id'): self.columns_mapping['user_id'] = 'user_id'
            else:
                self.columns_mapping = columns
        else:
            self.table_name = connector.get('table', 'logs')
            self.metadata = MetaData()
            
            if columns is None:
                self.columns_mapping = {
                    'timestamp': "timestamp",
                    'level': "levelname",
                    'logger_name': "name",
                    'message': "msg",
                }
            else:
                self.columns_mapping = columns

            db_columns = []
            if 'id' not in self.columns_mapping:
                db_columns.append(Column('id', Integer, primary_key=True))

            for col_name, _ in self.columns_mapping.items():
                if col_name == 'id':
                    continue
                elif col_name == 'timestamp':
                    db_columns.append(Column('timestamp', DateTime, default=func.now()))
                else:
                    db_columns.append(Column(col_name, String))

            self.log_table = Table(
                self.table_name,
                self.metadata,
                *db_columns
            )
            self.metadata.create_all(self.engine, checkfirst=True)

    def _create_engine(self, connector):
        engine_type = connector['engine']
        if engine_type == 'sqlite':
            filename = connector['filename']
            os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
            return create_engine(f"sqlite:///{filename}")
        elif engine_type == 'mysql':
            return create_engine(f"mysql+pymysql://{connector['user']}:{connector['password']}@{connector['host']}/{connector['database']}")
        else:
            raise ValueError(f"Unsupported database engine: {engine_type}")

    def _emit_sync(self, record):
        modified_record = self.formatter.apply_rules(record)
        if self.should_handle(modified_record):
            values_to_insert = {}
            for col_name, expr_str in self.columns_mapping.items():
                if col_name == 'id' and col_name not in modified_record:
                    continue
                
                column_obj = self.log_table.columns.get(col_name)
                if isinstance(column_obj.type, DateTime):
                    values_to_insert[col_name] = record['timestamp']
                    continue

                template = self.jinja_env.from_string(f"{{{{ {expr_str} }}}}")
                rendered_value = template.render(modified_record)

                if rendered_value == '' and column_obj.nullable:
                    values_to_insert[col_name] = None
                else:
                    values_to_insert[col_name] = rendered_value

            with self.engine.connect() as conn:
                ins = self.log_table.insert().values(**values_to_insert)
                conn.execute(ins)
                conn.commit()