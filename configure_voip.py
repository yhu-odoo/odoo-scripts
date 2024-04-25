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
        cur.execute(f'''
        SELECT count(*) FROM ir_config_parameter WHERE KEY = '{key}';
        ''')
        if cur.fetchone()[0] > 0:
            cur.execute(f'''
            UPDATE ir_config_parameter
            SET value = '{value}'
            WHERE KEY = '{key}';
            ''')
        else:
            cur.execute(f'''
            INSERT INTO ir_config_parameter(key, value)
            VALUES ('{key}', '{value}');
            ''')

    cur.execute(f'''
        UPDATE res_users_settings
        SET voip_username = '{USERNAME}', voip_secret = '{SECRET}'
        WHERE user_id = 2;
        ''')

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python configure_voip.py <database_name>")
        sys.exit(1)
    db = sys.argv[1]
    configure_voip(db)
