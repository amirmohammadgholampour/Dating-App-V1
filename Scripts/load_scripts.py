import json
from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey, create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker

db_url = URL.create(
    drivername="postgresql",
    username="postgres",
    password="0960034455",
    host="localhost",
    port=5432,
    database="dating_app"
)

engine = create_engine(db_url, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class UsersProvince(Base):
    __tablename__ = "users_province"

    id = Column(Integer, primary_key=True, autoincrement=True)
    province_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)


class UsersCity(Base):
    __tablename__ = "users_city"

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    province_id = Column(Integer, ForeignKey("users_province.id"), nullable=False)

def run_import():
    session = SessionLocal()

    try:
        print("Reading provinces.json...")
        with open("C:/Users/AmirMohammad/Desktop/Dating-App-V1/Scripts/provinces.json", "r", encoding="utf-8") as f:
            provinces_data = json.load(f)

        print("Reading cities.json...")
        with open("C:/Users/AmirMohammad/Desktop/Dating-App-V1/Scripts/cities.json", "r", encoding="utf-8") as f:
            cities_data = json.load(f)

        # Step 1: Ensure all provinces are inserted
        print("Importing provinces...")
        for p in provinces_data:
            prov_code = str(p.get("id"))
            exists = session.query(UsersProvince).filter(UsersProvince.province_id == prov_code).first()
            if not exists:
                province_obj = UsersProvince(
                    province_id=prov_code,
                    name=str(p.get("name"))
                )
                session.add(province_obj)

        session.commit()
        print("Provinces imported successfully.")

        # Step 2: Build a mapping from province_id (JSON) to database PK (id)
        province_map = {
            prov.province_id: prov.id
            for prov in session.query(UsersProvince).all()
        }

        # Step 3: Insert cities as strings
        print("Importing cities...")
        for c in cities_data:
            city_code = str(c.get("id"))
            prov_code = str(c.get("province_id"))

            target_province_db_id = province_map.get(prov_code)
            if target_province_db_id is None:
                continue

            exists = session.query(UsersCity).filter(UsersCity.city_id == city_code).first()
            if not exists:
                city_obj = UsersCity(
                    city_id=city_code,
                    name=str(c.get("name")),
                    province_id=target_province_db_id
                )
                session.add(city_obj)

        session.commit()
        print("Cities imported successfully.")

    except Exception as e:
        session.rollback()
        print(f"Error during execution: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    run_import()