"""Initial schema: trades, positions, signals, daily_pnl

Revision ID: 0001
Revises:
Create Date: 2026-06-15

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trades",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ibkr_exec_id", sa.String(50), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("exchange", sa.String(20), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("direction", sa.String(5), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("fill_price", sa.Numeric(12, 4), nullable=False),
        sa.Column("commission", sa.Numeric(10, 4), nullable=False, server_default="0"),
        sa.Column("fill_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("strategy_name", sa.String(100), nullable=False),
        sa.Column("eur_usd_rate", sa.Numeric(10, 6), nullable=True),
        sa.Column("pnl_usd", sa.Numeric(12, 4), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ibkr_exec_id", name="uq_trades_exec_id"),
    )
    op.create_index("ix_trades_symbol", "trades", ["symbol"])
    op.create_index("ix_trades_fill_time", "trades", ["fill_time"])

    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("exchange", sa.String(20), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_cost", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("current_price", sa.Numeric(12, 4), nullable=True),
        sa.Column("unrealized_pnl", sa.Numeric(12, 4), nullable=True),
        sa.Column("realized_pnl", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol", name="uq_positions_symbol"),
    )

    op.create_table(
        "signals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("direction", sa.String(5), nullable=False),
        sa.Column("strength", sa.Numeric(5, 4), nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("strategy_name", sa.String(100), nullable=False),
        sa.Column("stop_loss_pct", sa.Numeric(5, 4), nullable=True),
        sa.Column("take_profit_pct", sa.Numeric(5, 4), nullable=True),
        sa.Column(
            "acted_upon", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_signals_symbol_time", "signals", ["symbol", "generated_at"])

    op.create_table(
        "daily_pnl",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("realized_pnl", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("unrealized_pnl", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("num_trades", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("num_winning_trades", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_drawdown_pct", sa.Numeric(7, 4), nullable=True),
        sa.Column("portfolio_value", sa.Numeric(14, 4), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date", name="uq_daily_pnl_date"),
    )


def downgrade() -> None:
    op.drop_table("daily_pnl")
    op.drop_index("ix_signals_symbol_time", table_name="signals")
    op.drop_table("signals")
    op.drop_table("positions")
    op.drop_index("ix_trades_fill_time", table_name="trades")
    op.drop_index("ix_trades_symbol", table_name="trades")
    op.drop_table("trades")
