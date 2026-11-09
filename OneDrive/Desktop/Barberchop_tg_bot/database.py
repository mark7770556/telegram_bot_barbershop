import psycopg2
import os
from dotenv import load_dotenv
import html

from datetime import timedelta

load_dotenv()

def connect_whis_bd():
    try:
        conn = psycopg2.connect(host=os.getenv("DB_HOST"),port=int(os.getenv("DB_PORT")),dbname=os.getenv("DB_NAME"),user=os.getenv("DB_USER"),password=os.getenv("DB_PASSWORD"))
        cursor = conn.cursor()
        print("подключение удалось !!!")
        return conn,cursor
    except psycopg2.OperationalError as e :
        print("ошибка в подключении: ",e)
        return None,None

if __name__ == "__main__":
    print("подключение к бд")
    conn , cursor = connect_whis_bd()



def register_db(tg_id,rg_username,full_name,phone):
    conn , cursor = connect_whis_bd()
    if conn is None or cursor is None:
        return None
    try:
        sql = "insert into users(telegram_id,telegram_username,full_name,phone) values(%s,%s,%s,%s)  ON CONFLICT (telegram_id) DO UPDATE SET telegram_username = EXCLUDED.telegram_username, full_name = EXCLUDED.full_name, phone = COALESCE(EXCLUDED.phone, users.phone) returning id"
        cursor.execute(sql,(tg_id,rg_username,full_name,phone))
        user_id_for_zapis = cursor.fetchone()[0]
        conn.commit()
        return user_id_for_zapis
    except psycopg2.Error as e:
        conn.rollback()
        print("ошибка с бд: ",e)
        return None
    finally:
        cursor.close()
        conn.close()


def our_masters():
    conn , cursor = connect_whis_bd()
    if conn is None or cursor is None:
        return None
    try:
        sql = "select name, description from barbers WHERE is_active = TRUE ORDER BY name"
        cursor.execute(sql)
        masters = cursor.fetchall()
        if not masters:
            return "💈 Пока мастеров нет"
        result = ["💈 <b>НАШИ МАСТЕРА</b>\n"]
        for name, description in masters:
            result.append(f"✂️ <b>{html.escape(name)}</b>")
            if description:
                result.append(f"📝 {html.escape(description)}")
            result.append("━━━━━━━━━━━━━━")
        return "\n".join(result)
    except psycopg2.Error as e :
        print("ошибка с бд: ",e)
        return None
    finally:
        cursor.close()
        conn.close()

def check_id(tg_id):
    conn , cursor = connect_whis_bd()
    if conn is None or cursor is None:
        return None
    try:
        sql = "select count(*) from users where telegram_id = %s"
        cursor.execute(sql,(tg_id,))
        aaa = cursor.fetchone()[0]
        if aaa > 0:
            return True
        else:
            return False
    except psycopg2.Error as e :
        print("ошибка с бд: ",e)
        return None
    finally:
        cursor.close()
        conn.close()

def my_booking(tg_id):
    conn, cursor = connect_whis_bd()

    if conn is None or cursor is None:
        return None

    try:
        cursor.execute("""
            SELECT
                bk.id,
                b.name,
                bk.service_name_snapshot,
                bk.start_at,
                bk.status
            FROM bookings bk
            JOIN users u ON bk.user_id = u.id
            JOIN barbers b ON bk.barber_id = b.id
            WHERE u.telegram_id = %s
            ORDER BY bk.start_at DESC
        """, (tg_id,))

        bookings = cursor.fetchall()

        if not bookings:
            return None

        result = ["📋 <b>ВАШИ ЗАПИСИ</b>\n"]

        for booking_id, barber, service, start_at, status in bookings:
            result.append(
                f"🔹 Запись №{booking_id}\n"
                f"💈 Мастер: {html.escape(str(barber))}\n"
                f"✂️ Услуга: {html.escape(str(service))}\n"
                f"📅 Дата: {start_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"📌 Статус: {html.escape(str(status))}\n"
                f"━━━━━━━━━━━━━━"
            )

        return "\n".join(result)

    except psycopg2.Error as e:
        conn.rollback()
        print("Ошибка получения записей:", e)
        return None

    finally:
        cursor.close()
        conn.close()

def comments_author():
    conn, cursor = connect_whis_bd()
    if conn is None or cursor is None:
        return None

    try:
        cursor.execute("""
            SELECT b.name, r.comment
            FROM reviews r
            JOIN barbers b ON r.barber_id = b.id
            WHERE r.comment IS NOT NULL
              AND r.comment <> ''
            ORDER BY r.created_at DESC
        """)
        return cursor.fetchall()

    except psycopg2.Error as e:
        conn.rollback()
        print("Ошибка получения отзывов:", e)
        return None

    finally:
        cursor.close()
        conn.close()


def yslygi():
    conn , cursor = connect_whis_bd()
    if conn is None or cursor is None:
        return None
    try:
        sql = "SELECT name, COALESCE(NULLIF(description, ''), 'Описание отсутствует') AS description, price, duration_minutes FROM services WHERE is_active = TRUE ORDER BY id"
        cursor.execute(sql)
        a = cursor.fetchall()
        return a
    except Exception as e:
        print("Ошибка отзывов:", e)
        return None
    finally:
        cursor.close()
        conn.close()







def get_services():
    conn, cursor = connect_whis_bd()

    if conn is None or cursor is None:
        return None

    try:
        cursor.execute("""
            SELECT id, name, price, duration_minutes
            FROM services
            WHERE is_active = TRUE
            ORDER BY id
        """)
        return cursor.fetchall()

    except psycopg2.Error as e:
        conn.rollback()
        print("Ошибка получения услуг:", e)
        return None

    finally:
        cursor.close()
        conn.close()
def get_barbers():
    conn, cursor = connect_whis_bd()

    if conn is None or cursor is None:
        return None

    try:
        cursor.execute("""
            SELECT id, name
            FROM barbers
            WHERE is_active = TRUE
            ORDER BY id
        """)
        return cursor.fetchall()

    except psycopg2.Error as e:
        conn.rollback()
        print("Ошибка получения мастеров:", e)
        return None

    finally:
        cursor.close()
        conn.close()
def create_booking(telegram_id, username, full_name,
                   barber_id, service_id, start_at):

    conn, cursor = connect_whis_bd()

    if conn is None or cursor is None:
        return ("error",)

    try:
        cursor.execute("""
            SELECT name, price, duration_minutes
            FROM services
            WHERE id = %s AND is_active = TRUE
        """, (service_id,))

        service = cursor.fetchone()

        if not service:
            return ("invalid",)

        cursor.execute("""
            SELECT name
            FROM barbers
            WHERE id = %s AND is_active = TRUE
        """, (barber_id,))

        barber = cursor.fetchone()

        if not barber:
            return ("invalid",)

        service_name, price, duration = service
        barber_name = barber[0]

        end_at = start_at + timedelta(minutes=duration)

        cursor.execute("""
            INSERT INTO users (
                telegram_id,
                telegram_username,
                full_name
            )
            VALUES (%s, %s, %s)
            ON CONFLICT (telegram_id)
            DO UPDATE SET
                telegram_username = EXCLUDED.telegram_username,
                full_name = EXCLUDED.full_name
            RETURNING id
        """, (telegram_id, username, full_name))

        user_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO bookings (
                user_id,
                barber_id,
                service_id,
                start_at,
                end_at,
                status,
                service_name_snapshot,
                price_snapshot,
                duration_minutes_snapshot
            )
            VALUES (%s, %s, %s, %s, %s, 'pending', %s, %s, %s)
            RETURNING id
        """, (
            user_id,
            barber_id,
            service_id,
            start_at,
            end_at,
            service_name,
            price,
            duration
        ))

        booking_id = cursor.fetchone()[0]

        conn.commit()

        return (
            "ok",
            booking_id,
            service_name,
            price,
            duration,
            barber_name,
            end_at
        )

    except psycopg2.errors.ExclusionViolation:
        conn.rollback()
        return ("occupied",)

    except psycopg2.Error as e:
        conn.rollback()
        print("Ошибка создания записи:", e)
        return ("error",)

    finally:
        cursor.close()
        conn.close()

def add_service(name, description, price, duration):
    conn, cursor = connect_whis_bd()

    if conn is None or cursor is None:
        return False

    try:
        cursor.execute("""
            INSERT INTO services (name, description, price, duration_minutes)
            VALUES (%s, %s, %s, %s)
        """, (name, description, price, duration))

        conn.commit()
        return True

    except psycopg2.Error as e:
        conn.rollback()
        print("Ошибка добавления услуги:", e)
        return False

    finally:
        cursor.close()
        conn.close()
def add_barber(name, description):
    conn, cursor = connect_whis_bd()

    if conn is None or cursor is None:
        return False

    try:
        cursor.execute("""
            INSERT INTO barbers (name, description)
            VALUES (%s, %s)
        """, (name, description))

        conn.commit()
        return True

    except psycopg2.Error as e:
        conn.rollback()
        print("Ошибка добавления мастера:", e)
        return False

    finally:
        cursor.close()
        conn.close()
def get_all_bookings():
    conn, cursor = connect_whis_bd()
    if conn is None or cursor is None:
        return None

    try:
        cursor.execute("""
            SELECT
                bk.id,
                u.telegram_id,
                u.full_name,
                b.name,
                bk.service_name_snapshot,
                bk.start_at,
                bk.status
            FROM bookings bk
            JOIN users u ON bk.user_id = u.id
            JOIN barbers b ON bk.barber_id = b.id
            WHERE bk.status IN ('pending', 'confirmed')
              AND bk.end_at > NOW() - INTERVAL '1 hour'
            ORDER BY bk.start_at ASC
            LIMIT 50
        """)
        return cursor.fetchall()

    except psycopg2.Error as e:
        conn.rollback()
        print("Ошибка получения записей:", e)
        return None

    finally:
        cursor.close()
        conn.close()
def cancel_booking(booking_id):
    conn, cursor = connect_whis_bd()

    if conn is None or cursor is None:
        return None

    try:
        cursor.execute("""
            UPDATE bookings bk
            SET status = 'cancelled',
                updated_at = NOW()
            FROM users u
            WHERE bk.id = %s
              AND bk.user_id = u.id
              AND bk.status IN ('pending', 'confirmed')
            RETURNING
                u.telegram_id,
                bk.id,
                bk.service_name_snapshot,
                bk.start_at
        """, (booking_id,))

        result = cursor.fetchone()
        conn.commit()

        return result

    except psycopg2.Error as e:
        conn.rollback()
        print("Ошибка отмены записи:", e)
        return None

    finally:
        cursor.close()
        conn.close()
def get_client(telegram_id):
    conn, cursor = connect_whis_bd()

    if conn is None or cursor is None:
        return None

    try:
        cursor.execute("""
            SELECT telegram_id, full_name
            FROM users
            WHERE telegram_id = %s
        """, (telegram_id,))

        return cursor.fetchone()

    except psycopg2.Error as e:
        conn.rollback()
        print("Ошибка поиска клиента:", e)
        return None

    finally:
        cursor.close()
        conn.close()


def add_review(telegram_id, barber_id, rating, comment):
    conn, cursor = connect_whis_bd()

    if conn is None or cursor is None:
        return False

    try:
        cursor.execute("""
            INSERT INTO reviews (telegram_id, barber_id, rating, comment)
            VALUES (%s, %s, %s, %s)
        """, (telegram_id, barber_id, rating, comment))

        conn.commit()
        return True

    except psycopg2.Error as e:
        conn.rollback()
        print("Ошибка сохранения отзыва:", e)
        return False

    finally:
        cursor.close()
        conn.close()


def get_clients_with_bookings(limit=10, offset=0):
    conn, cursor = connect_whis_bd()

    if conn is None or cursor is None:
        return None

    try:
        cursor.execute("""
            SELECT
                u.telegram_id,
                u.full_name,
                u.telegram_username,
                COUNT(bk.id) AS bookings_count,
                MAX(bk.start_at) AS last_booking
            FROM users u
            JOIN bookings bk ON bk.user_id = u.id
            GROUP BY
                u.telegram_id,
                u.full_name,
                u.telegram_username
            ORDER BY MAX(bk.start_at) DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))

        return cursor.fetchall()

    except psycopg2.Error as e:
        conn.rollback()
        print("Ошибка получения клиентов:", e)
        return None

    finally:
        cursor.close()
        conn.close()

        
def get_client_bookings(telegram_id):
    conn, cursor = connect_whis_bd()

    if conn is None or cursor is None:
        return None

    try:
        cursor.execute("""
            SELECT
                u.full_name,
                u.telegram_username,
                bk.id,
                bk.service_name_snapshot,
                b.name,
                bk.start_at,
                bk.end_at,
                bk.status
            FROM users u
            JOIN bookings bk ON bk.user_id = u.id
            JOIN barbers b ON b.id = bk.barber_id
            WHERE u.telegram_id = %s
            ORDER BY bk.start_at DESC
        """, (telegram_id,))

        return cursor.fetchall()

    except psycopg2.Error as e:
        conn.rollback()
        print("Ошибка получения истории клиента:", e)
        return None

    finally:
        cursor.close()
        conn.close()


def cleanup_old_bookings():
    conn, cursor = connect_whis_bd()

    if conn is None or cursor is None:
        return False

    try:
        cursor.execute("""
            DELETE FROM bookings
            WHERE end_at <= NOW() - INTERVAL '7 days'
        """)

        deleted_count = cursor.rowcount
        conn.commit()
        print(f"Удалено старых записей: {deleted_count}")
        return True

    except psycopg2.Error as e:
        conn.rollback()
        print("Ошибка очистки старых записей:", e)
        return False

    finally:
        cursor.close()
        conn.close()

def update_telegram_username(telegram_id, username):
    conn, cursor = connect_whis_bd()

    if conn is None or cursor is None:
        return False

    try:
        cursor.execute("""
            UPDATE users
            SET telegram_username = %s
            WHERE telegram_id = %s
        """, (username, telegram_id))

        conn.commit()
        return True

    except psycopg2.Error as e:
        conn.rollback()
        print("Ошибка обновления username:", e)
        return False

    finally:
        cursor.close()
        conn.close()


def get_pending_bookings():
    conn, cursor = connect_whis_bd()

    if conn is None or cursor is None:
        return None

    try:
        cursor.execute("""
            SELECT
                bk.id,
                u.telegram_id,
                u.full_name,
                b.name,
                bk.service_name_snapshot,
                bk.start_at
            FROM bookings bk
            JOIN users u ON u.id = bk.user_id
            JOIN barbers b ON b.id = bk.barber_id
            WHERE bk.status = 'pending'
            ORDER BY bk.start_at ASC
        """)

        return cursor.fetchall()

    except psycopg2.Error as e:
        conn.rollback()
        print("Ошибка получения ожидающих записей:", e)
        return None

    finally:
        cursor.close()
        conn.close()


def confirm_booking(booking_id):
    conn, cursor = connect_whis_bd()

    if conn is None or cursor is None:
        return None

    try:
        cursor.execute("""
            UPDATE bookings bk
            SET status = 'confirmed',
                updated_at = NOW()
            FROM users u
            WHERE bk.id = %s
              AND bk.user_id = u.id
              AND bk.status = 'pending'
            RETURNING
                u.telegram_id,
                bk.id,
                bk.service_name_snapshot,
                bk.start_at
        """, (booking_id,))

        result = cursor.fetchone()
        conn.commit()

        return result

    except psycopg2.Error as e:
        conn.rollback()
        print("Ошибка подтверждения записи:", e)
        return None

    finally:
        cursor.close()
        conn.close()

