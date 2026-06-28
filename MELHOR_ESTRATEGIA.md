# Melhor estratégia — análise de combinações

Documento gerado a partir de um benchmark controlado das combinações de estratégias
do otimizador de rotas (`tsp.py` / `genetic_algorithm.py`).

## Metodologia

- **Instância fixa** (mesma para todas as combinações): `random.seed(42)` antes de
  `build_cities()` — 15 clientes + hospital, frota de 4 veículos (capacidade 100,
  autonomia 1200). Comparar resultados na mesma instância é o que torna o teste justo.
- **Parâmetros**: população 100, intensidade de ajuste local (mutação) 0.6.
- **315 combinações** = 5 construções iniciais × 3 seleções × 3 recombinações × 7 ajustes locais.
- **Estágio 1**: 400 ciclos, 1 execução por combinação (ranqueamento rápido).
- **Estágio 2**: top 8 revalidado com 3000 ciclos × 4 sementes (11, 22, 33, 44),
  escolhendo pelo **menor custo médio**.

## Conclusão

**Não há combinação que gere resultado melhor.** Para esta instância, o custo ótimo é
**14424.8** e é atingido de forma confiável por várias combinações (14 das 15 melhores
do estágio 1 já empatam nesse valor). No estágio 2, as melhores combinações atingem
14424.8 em **todas as 4 sementes, com variância zero**. A qualidade final, portanto,
empata no ótimo; o que muda entre as combinações é a velocidade/robustez de convergência,
não o custo final.

> Observação: isso é consequência do tamanho pequeno do problema (15 clientes). Em
> instâncias maiores (ex.: dezenas/centenas de cidades) as combinações tenderiam a
> divergir em qualidade, e este benchmark deveria ser refeito na instância-alvo.

## Estratégia utilizada para gerar o melhor resultado

A combinação mais robusta (atingiu o ótimo em todas as sementes, menor custo médio):

| Dimensão              | Escolha       | Descrição no relatório                   |
|-----------------------|---------------|------------------------------------------|
| Construção inicial    | `random`      | Aleatória                                |
| Seleção               | `tournament`  | Por disputa entre planos candidatos      |
| Recombinação          | `ox`          | Preservando a ordem das visitas          |
| Ajuste local (mutação)| `swap`        | Troca de duas paradas                    |

- **Custo final**: 14424.8 (ótimo) — custos por semente: [14424.8, 14424.8, 14424.8, 14424.8].

Empata com ela, igualmente ótima e estável: `hull + rank + pmx + swap`.

## Ranking do estágio 2 (por custo médio)

```
média=  14424.8  init=random  sel=tournament cross=ox   mut=swap
média=  14424.8  init=hull    sel=rank       cross=pmx  mut=swap
média=  14479.0  init=random  sel=rank       cross=ox   mut=inversion
média=  14479.0  init=random  sel=rank       cross=cx   mut=random
média=  14576.9  init=random  sel=tournament cross=ox   mut=reallocate
média=  14682.6  init=random  sel=rank       cross=pmx  mut=random
média=  14866.6  init=random  sel=rank       cross=ox   mut=reallocate
média=  14958.6  init=random  sel=rank       cross=cx   mut=scramble
```
