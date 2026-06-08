import pandas as pd

df = pd.read_csv("dados_vendas.csv", parse_dates=["data"])

vendidos = df[df["status"] == "Vendido"]

total_vendas = len(vendidos)
receita_total = vendidos["valor"].sum()
ticket_medio = vendidos["valor"].mean()

ranking_vendedores = (
    vendidos.groupby("vendedor")
    .size()
    .sort_values(ascending=False)
    .reset_index(name="vendas")
)

modelos_mais_vendidos = (
    vendidos.groupby("modelo")
    .size()
    .sort_values(ascending=False)
    .reset_index(name="vendas")
)

SEP = "=" * 48

print(SEP)
print("       ANALISE DE VENDAS - CONCESSIONARIA")
print(SEP)

print(f"\n{'Total de vendas realizadas:':<30} {total_vendas}")
print(f"{'Receita total (vendidos):':<30} R$ {receita_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
print(f"{'Ticket medio:':<30} R$ {ticket_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

print(f"\n{'-' * 48}")
print("  RANKING DE VENDEDORES")
print(f"{'-' * 48}")
print(f"  {'#':<4} {'Vendedor':<25} {'Vendas':>6}")
print(f"  {'-'*4} {'-'*25} {'-'*6}")
for i, row in ranking_vendedores.iterrows():
    print(f"  {i+1:<4} {row['vendedor']:<25} {row['vendas']:>6}")

print(f"\n{'-' * 48}")
print("  MODELOS MAIS VENDIDOS")
print(f"{'-' * 48}")
print(f"  {'#':<4} {'Modelo':<20} {'Vendas':>6}")
print(f"  {'-'*4} {'-'*20} {'-'*6}")
for i, row in modelos_mais_vendidos.iterrows():
    print(f"  {i+1:<4} {row['modelo']:<20} {row['vendas']:>6}")

print(f"\n{SEP}\n")
