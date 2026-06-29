from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select

from app.config import settings
from app.models import Base, User, AlertSettings, SourceMaster

_connect_args = {"check_same_thread": False} if settings.is_sqlite else {}

engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args=_connect_args,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

SOURCE_SEED = [
    ("팜맵 조회", "제1유형"),
    ("팜맵 농업기상", "제1유형"),
    ("팜맵 토양검정", "제1유형"),
    ("팜맵 병해충발생", "제1유형"),
    ("기상청 단기예보", "제1유형"),
    ("농사로 병해충발생", "제3유형", False),
    ("농사로 농약등록", "제3유형", False),
    ("토양검정 V2", "제1유형"),
    ("비료사용처방", "제1유형"),
]


async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        result = await session.execute(select(User).limit(1))
        if not result.scalar_one_or_none():
            user = User(name="데모 농가", region="경상북도")
            session.add(user)
            await session.flush()
            session.add(AlertSettings(user_id=user.user_id))

        src_result = await session.execute(select(SourceMaster).limit(1))
        if not src_result.scalar_one_or_none():
            for entry in SOURCE_SEED:
                name, license_type = entry[0], entry[1]
                commercial = entry[2] if len(entry) > 2 else True
                session.add(SourceMaster(
                    source_name=name,
                    license_type=license_type,
                    commercial_allowed=commercial,
                    last_status="unknown",
                ))
        else:
            existing = {s.source_name for s in (await session.execute(select(SourceMaster))).scalars().all()}
            for entry in SOURCE_SEED:
                name, license_type = entry[0], entry[1]
                if name not in existing:
                    commercial = entry[2] if len(entry) > 2 else True
                    session.add(SourceMaster(
                        source_name=name, license_type=license_type,
                        commercial_allowed=commercial, last_status="unknown",
                    ))

        await session.commit()
