import psycopg2
import sys


SERVER_CONFIGURATION = {
    'voip.wsServer': '',
    'voip.pbx_ip': '',
    'voip.mode': '',
}
USERNAME = ''
SECRET = ''

def configure_voip(db):
    conn = psycopg2.connect(
        dbname=db,
        user="odoo")
    cur = conn.cursor()

    for key, value in SERVER_CONFIGURATION.items():
        cur.execute('''
        SELECT count(*) FROM ir_config_parameter WHERE KEY = '{}';
        '''.format(key))
        if cur.fetchone()[0] > 0:
            cur.execute('''
            UPDATE ir_config_parameter
            SET value = '{}'
            WHERE KEY = '{}';
            '''.format(value, key))
        else:
            cur.execute('''
            INSERT INTO ir_config_parameter(key, value)
            VALUES ('{}', '{}');
            '''.format(key, value))

    cur.execute('''
        UPDATE res_users_settings
        SET voip_username = '{}', voip_secret = '{}'
        WHERE user_id = 2;
        '''.format(USERNAME, SECRET))

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python configure_voip.py <database_name>")
        sys.exit(1)
    db = sys.argv[1]
    configure_voip(db)
