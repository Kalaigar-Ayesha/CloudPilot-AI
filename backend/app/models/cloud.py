import uuid
from sqlalchemy import String, ForeignKey, JSON, Boolean, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CloudAccount(Base):
    """
    CloudAccount model representing user integrated cloud credentials configurations.
    """
    __tablename__ = "cloud_accounts"

    project_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    provider_id: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_identifier: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="CONNECTED", nullable=False)

    # Relationships
    credentials: Mapped["CloudCredentials"] = relationship(
        "CloudCredentials",
        back_populates="account",
        cascade="all, delete-orphan",
        uselist=False
    )
    resources: Mapped[list["Resource"]] = relationship(
        "Resource",
        back_populates="account",
        cascade="all, delete-orphan"
    )


class CloudCredentials(Base):
    """
    CloudCredentials storing encrypted authentication parameters.
    """
    __tablename__ = "cloud_credentials"

    cloud_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cloud_accounts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    encrypted_payload: Mapped[str] = mapped_column(nullable=False)
    key_arn: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationship
    account: Mapped[CloudAccount] = relationship(
        "CloudAccount",
        back_populates="credentials"
    )


class Resource(Base):
    """
    Resource base model containing unified attributes discovered across clouds.
    """
    __tablename__ = "resources"

    cloud_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cloud_accounts.id", ondelete="CASCADE"),
        nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    tags: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Relationship
    account: Mapped[CloudAccount] = relationship(
        "CloudAccount",
        back_populates="resources"
    )
    
    # Sub-type concrete relationships
    compute: Mapped["ComputeResource"] = relationship(
        "ComputeResource",
        back_populates="resource",
        cascade="all, delete-orphan",
        uselist=False
    )
    storage: Mapped["StorageResource"] = relationship(
        "StorageResource",
        back_populates="resource",
        cascade="all, delete-orphan",
        uselist=False
    )
    database: Mapped["DatabaseResource"] = relationship(
        "DatabaseResource",
        back_populates="resource",
        cascade="all, delete-orphan",
        uselist=False
    )
    networking: Mapped["NetworkingResource"] = relationship(
        "NetworkingResource",
        back_populates="resource",
        cascade="all, delete-orphan",
        uselist=False
    )


class ComputeResource(Base):
    """Compute concrete resource metadata properties."""
    __tablename__ = "compute_resources"

    resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    instance_type: Mapped[str] = mapped_column(String(100), nullable=False)
    vcpu_count: Mapped[int] = mapped_column(Integer, nullable=False)
    memory_gb: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    operating_system: Mapped[str] = mapped_column(String(100), nullable=False)
    lifecycle: Mapped[str] = mapped_column(String(50), nullable=False)  # ON_DEMAND, SPOT, RESERVED

    # Relationship
    resource: Mapped[Resource] = relationship(
        "Resource",
        back_populates="compute"
    )


class StorageResource(Base):
    """Storage concrete resource metadata properties."""
    __tablename__ = "storage_resources"

    resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    size_gb: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    storage_type: Mapped[str] = mapped_column(String(100), nullable=False)
    iops: Mapped[int | None] = mapped_column(Integer, nullable=True)
    throughput_mbps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    encrypted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationship
    resource: Mapped[Resource] = relationship(
        "Resource",
        back_populates="storage"
    )


class DatabaseResource(Base):
    """Database concrete resource metadata properties."""
    __tablename__ = "database_resources"

    resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    engine: Mapped[str] = mapped_column(String(100), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(50), nullable=False)
    instance_class: Mapped[str] = mapped_column(String(100), nullable=False)
    multi_az: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    storage_size_gb: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Relationship
    resource: Mapped[Resource] = relationship(
        "Resource",
        back_populates="database"
    )


class NetworkingResource(Base):
    """Networking concrete resource metadata properties."""
    __tablename__ = "networking_resources"

    resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    vpc_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cidr_block: Mapped[str | None] = mapped_column(String(50), nullable=True)
    public_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    load_balancer_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationship
    resource: Mapped[Resource] = relationship(
        "Resource",
        back_populates="networking"
    )
