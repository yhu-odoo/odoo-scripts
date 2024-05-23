SERVER_CONFIGURATION = {
    'voip.wsServer': '',
    'voip.pbx_ip': '',
    'voip.mode': '',
}
USERNAME = ''
SECRET = ''
ODOO_PATH = ''


import psycopg2
import re
import sys
sys.path.append(ODOO_PATH)
import odoo


def configure_voip(db):
    conn = psycopg2.connect(
        dbname=db,
        user="odoo")
    cur = conn.cursor()

    version = re.match(r"[\d\.]+", odoo.release.version).group(0)
    if version < "17.2":
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
    else:
        cur.execute('''
            SELECT id FROM voip_provider WHERE name = 'Default';
        ''')
        row = cur.fetchone()
        if row:
            provider_id = row[0]
            cur.execute(f'''
                UPDATE voip_provider SET
                    name = 'Default',
                    ws_server = '{SERVER_CONFIGURATION["voip.wsServer"]}',
                    pbx_ip = '{SERVER_CONFIGURATION["voip.pbx_ip"]}',
                    mode = '{SERVER_CONFIGURATION["voip.mode"]}'
                WHERE id = {provider_id};
            ''')
        else:
            cur.execute(f'''
                INSERT INTO voip_provider (name, ws_server, pbx_ip, mode)
                VALUES ('Default', '{SERVER_CONFIGURATION["voip.wsServer"]}', '{SERVER_CONFIGURATION["voip.pbx_ip"]}', '{SERVER_CONFIGURATION["voip.mode"]}');
            ''')
            cur.execute('''
                SELECT id FROM voip_provider WHERE name = 'Default';
            ''')
            provider_id = cur.fetchone()[0]

        cur.execute(f'''
            UPDATE res_users_settings
            SET voip_provider_id = '{provider_id}', voip_username = '{USERNAME}', voip_secret = '{SECRET}'
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
