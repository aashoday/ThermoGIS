import uuid
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from app.database import Base

class IndustrialAsset(Base):
    __tablename__ = "industrial_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=True)
    asset_type = Column(String, nullable=False)       # 'refinery', 'mine', 'plant', etc. (from OSM tags)
    source = Column(String, nullable=False, default="OSM")
    geom = Column(Geometry(geometry_type="GEOMETRY", srid=4326), nullable=False)  # point OR polygon