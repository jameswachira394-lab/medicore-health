import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared_common.database import Base


class InvoiceStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    CARD = "card"
    MOBILE_MONEY = "mobile_money"
    INSURANCE = "insurance"
    CASH = "cash"


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    appointment_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)

    total_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    amount_paid: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus), default=InvoiceStatus.PENDING)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    line_items: Mapped[list["InvoiceLineItem"]] = relationship(back_populates="invoice", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id: Mapped[str] = mapped_column(String(36), ForeignKey("invoices.id"), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. "Consultation", "Lab test"
    amount: Mapped[float] = mapped_column(Float, nullable=False)

    invoice: Mapped["Invoice"] = relationship(back_populates="line_items")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id: Mapped[str] = mapped_column(String(36), ForeignKey("invoices.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(255), nullable=True)  # gateway transaction id
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    invoice: Mapped["Invoice"] = relationship(back_populates="payments")


class InsuranceClaim(Base):
    __tablename__ = "insurance_claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id: Mapped[str] = mapped_column(String(36), ForeignKey("invoices.id"), nullable=False)
    insurer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    policy_number: Mapped[str] = mapped_column(String(100), nullable=False)
    claim_amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="submitted")  # submitted | approved | rejected | paid
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
