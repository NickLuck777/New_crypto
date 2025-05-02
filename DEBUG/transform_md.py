import pandas as pd
import inflection
import logging
from datetime import datetime

def transform_rss(msgs):
    logging.info(f'Transforming messages...')
    logging.info(f'Message count: {len(msgs)}')
    try:
        df = pd.DataFrame(msgs)
    except Exception as e:
        logging.error(f"Failed to create DataFrame from messages: {e}")
        return None

    logging.info('Deleting columns...')
    try:
        df = df[['id', 'title', 'published', 'sentiment']]
    except KeyError as e:
        logging.error(f"Missing expected columns: {e}")
    logging.info('Deleting columns... done.')

    logging.info('Cast published to DateTime...')
    try:
        # Приводим первые буквы дня недели и месяца к заглавным для соответствия формату
        df['published'] = df['published'].apply(
            lambda date_string: datetime.strptime(
            ' '.join(word.capitalize() if i in [0, 2] else word for i, word in enumerate(date_string.split())).replace('gmt', '+0000').replace('GMT', '+0000'),
                '%a, %d %b %Y %H:%M:%S %z'
        ).strftime('%Y-%m-%d %H:%M:%S')
        )
    except Exception as e:
        logging.error(f"Error parsing date in 'published' column: {e}")
        df['published'] = '1970-01-01 00:00:00'  # Значение по умолчанию при ошибке
    logging.info('Cast published to DateTime... done.')

    logging.info('Casting the columns types...')
    try:
        df['published'] = pd.to_datetime(df['published'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        df['sentiment'] = df['sentiment'].astype('float64', errors='ignore')
        df['id'] = df['id'].astype(str)
        df['title'] = df['title'].astype(str)
    except Exception as e:
        logging.error(f"Error casting column types: {e}")
    logging.info('Casting the columns types... done.')

    logging.info('Columns transformation...')
    try:
        df.columns = [inflection.underscore(col) for col in df.columns]
    except Exception as e:
        logging.error(f"Error transforming columns: {e}")
    logging.info('Columns transformation... done.')

    logging.info('Drop duplicates...')
    try:
        df.drop_duplicates(subset=['id'], inplace=True)
    except Exception as e:
        logging.error(f"Error dropping duplicates: {e}")
    logging.info('Drop duplicates... done.')

    logging.info('Fill empty values...')
    try:
        numeric_columns = df.select_dtypes(include=['int64', 'float64', 'datetime64']).columns
        string_columns = df.select_dtypes(include=['object']).columns
        df[numeric_columns] = df[numeric_columns].fillna(0)
        df[string_columns] = df[string_columns].fillna('N/A')
    except Exception as e:
        logging.error(f"Error filling empty values: {e}")
    logging.info('Fill empty values... done.')

    logging.info('Removing newlines and tabs...')
    try:
        df[string_columns] = df[string_columns].apply(lambda col: col.str.replace('\\n', ''))
        df[string_columns] = df[string_columns].apply(lambda col: col.str.replace('\\t', ' '))
        df[string_columns] = df[string_columns].apply(lambda col: col.str.replace(' {2,}', ' ', regex=True))
        df[string_columns] = df[string_columns].apply(lambda col: col.str.strip())
    except Exception as e:
        logging.error(f"Error removing newlines and tabs: {e}")
    logging.info('Removing newlines and tabs... done.')

    logging.info('Delete emodji...')
    try:
        df = df.astype(str).map(lambda x: x.encode('ascii', 'ignore').decode('ascii'))
    except Exception as e:
        logging.error(f"Error deleting emodji: {e}")
    logging.info('Delete emodji... done.')

    logging.info('To lowercase...')
    try:
        df[string_columns] = df[string_columns].apply(lambda col: col.str.lower())
    except Exception as e:
        logging.error(f"Error converting to lowercase: {e}")
    logging.info('To lowercase... done.')

    logging.info('Transforming messages... done.')
    return df

def transform_eth_trx(msgs):
    logging.info('Transforming messages...')
    try:
        df = pd.DataFrame(msgs)
    except Exception as e:
        logging.error(f"Failed to create DataFrame from messages: {e}")
        return None

    logging.info('Columns transformation...')
    try:
        df.columns = [inflection.underscore(col) for col in df.columns]
    except Exception as e:
        logging.error(f"Error transforming columns: {e}")
    logging.info('Columns transformation... done.')

    logging.info('Drop duplicates...')
    try:
        df.drop_duplicates(subset=['hash'], inplace=True)
    except Exception as e:
        logging.error(f"Error dropping duplicates: {e}")
    logging.info('Drop duplicates... done.')

    logging.info('Fill empty values...')
    try:
        numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
        string_columns = df.select_dtypes(include=['object']).columns
        df[numeric_columns] = df[numeric_columns].fillna(0)
        df[string_columns] = df[string_columns].fillna('N/A')
        print(df[numeric_columns].info())
        print(df[string_columns].info())
    except Exception as e:
        logging.error(f"Error filling empty values: {e}")
    logging.info('Fill empty values... done.')

    logging.info('Removing newlines and tabs...')
    try:
        df[string_columns] = df[string_columns].apply(lambda col: col.str.replace('\\n', ''))
        df[string_columns] = df[string_columns].apply(lambda col: col.str.replace('\\t', ' '))
        df[string_columns] = df[string_columns].apply(lambda col: col.str.replace(' {2,}', ' ', regex=True))
        df[string_columns] = df[string_columns].apply(lambda col: col.str.strip())
    except Exception as e:
        logging.error(f"Error removing newlines and tabs: {e}")
    logging.info('Removing newlines and tabs... done.')

    logging.info('To lowercase...')
    try:
        df[string_columns] = df[string_columns].apply(lambda col: col.str.lower())
    except Exception as e:
        logging.error(f"Error converting to lowercase: {e}")
    logging.info('To lowercase... done.')

    logging.info('Transforming messages... done.')
    return df.to_dict(orient='records')
