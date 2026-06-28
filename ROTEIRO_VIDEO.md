# Roteiro de Vídeo — Algoritmo Genético para o VRP Hospitalar

**Duração-alvo:** ~10 min (flexível entre 8 e 12) · **Público:** misto (intuitivo → técnico) ·
**Formato:** narração + slides/overlays de código + **demo ao vivo** da visualização Pygame.

> Cada bloco traz: ⏱️ tempo · 🎙️ *fala* (o que narrar) · 🖥️ **TELA** (o que mostrar/fazer).
> O conteúdo é fiel ao código: `genetic_algorithm.py`, `tsp.py`, `draw_functions.py` e `SPEC.md`.

---

## ⏱️ [0:00–0:45] Abertura e gancho

🎙️ "Como entregar medicamentos de um hospital para vários pontos da cidade, com poucos veículos,
sem estourar a capacidade de carga nem a autonomia — e ainda priorizando o que é urgente? Esse é o
**Problema de Roteamento de Veículos (VRP)**, e neste vídeo vamos resolvê-lo com um **algoritmo
genético**." Apresentar nome/equipe/disciplina.

🖥️ Título na tela + a janela do programa já rodando ao fundo, com as rotas coloridas se formando.

---

## ⏱️ [0:45–2:00] O problema (intuição)

🎙️ O VRP é uma evolução do clássico "caixeiro viajante", mas mais realista: em vez de **um** trajeto,
temos uma **frota** saindo de um depósito central — aqui, o **Hospital** — e cada veículo tem
**restrições do mundo real**:
- **Capacidade de carga**: o veículo só leva até X kg/unidades.
- **Autonomia**: distância máxima por viagem (combustível/bateria), contando a volta ao hospital.
- **Prioridade**: medicamentos **críticos** precisam chegar antes de insumos de rotina.

🖥️ Slide/diagrama simples: 1 hospital no centro, vários pontos de entrega, 2–3 veículos. Destacar
visualmente um ponto "crítico".

---

## ⏱️ [2:00–3:15] O que é um algoritmo genético

🎙️ Inspiração na **seleção natural**: mantemos uma **população** de soluções candidatas; as melhores
"sobrevivem" e "se reproduzem", e ao longo de várias **gerações** a qualidade média melhora. Para
montar um AG precisamos de **4 ingredientes**, que vamos detalhar a seguir:
1. **Representação** (como codificar uma solução)
2. **Fitness** (como medir se é boa)
3. **Seleção** (quem reproduz)
4. **Operadores** (crossover + mutação, que geram filhos)

🖥️ Slide com os 4 ingredientes em destaque (eles guiam os próximos blocos).

---

## ⏱️ [3:15–4:15] Ingrediente 1 — Representação (o cromossomo)

🎙️ Cada solução é uma **lista de IDs de cidades** — uma ordem de visita, por exemplo `[3, 1, 5, 2, 4]`.
O **Hospital tem ID 0 e não entra na lista** (ele é sempre o início e o fim). Cada cidade carrega
posição, **demanda** (carga) e **prioridade** (10 = crítico, 1 = regular).

🖥️ Overlay de `genetic_algorithm.py`: dataclasses `City(id, x, y, demand, priority)` e
`FleetConfig(num_vehicles, vehicle_capacity, vehicle_autonomy)` + uma lista de exemplo.

---

## ⏱️ [4:15–5:15] Ingrediente bônus — De cromossomo para rotas (`split_routes`)

🎙️ Aqui está o "pulo do gato": o cromossomo é só **uma ordem**. Quem decide **quantos veículos** e
**onde corta cada rota** é a função `split_routes`, de forma **gulosa** — vai enchendo um veículo
com clientes na ordem da lista até que o próximo **estoure a capacidade ou a autonomia** (já contando
a volta ao hospital); aí ela "fecha" esse veículo e abre o próximo. Ou seja, **o número de veículos
emerge da solução** — não está fixado no cromossomo.

🖥️ Animação/diagrama de uma lista sendo "cortada" em 2–3 rotas; opcionalmente mostrar a função.

---

## ⏱️ [5:15–6:30] Ingrediente 2 — Fitness (qualidade + penalidades)

🎙️ Queremos **minimizar** um **custo total**:

```
custo = distância_total
      + penalidade_prioridade   (prioridade × distância acumulada até o cliente)
      + penalidade_capacidade   (excesso de carga × 1000)
      + penalidade_autonomia    (excesso de distância × 1000)
      + penalidade_frota        (veículos além do limite × 5000)
```

Em linguagem simples: somamos a distância de todas as rotas; **punimos** entregar um item urgente
muito tarde (prioridade alta atendida no fim da rota custa caro); e aplicamos **multas pesadas**
quando uma rota estoura carga, autonomia, ou quando precisamos de mais veículos do que a frota tem.
As multas são propositalmente grandes para **empurrar a evolução rumo a soluções viáveis**.

🖥️ A fórmula (docstring de `calculate_fitness` / `SPEC.md`), com cada termo aparecendo; apontar no
**dashboard** os alertas "SOBRECARGA" / "AUTONOMIA EXCEDIDA" quando ocorrerem na demo.

---

## ⏱️ [6:30–7:45] Ingredientes 3 e 4 — Seleção, crossover e mutação

🎙️ Como cada geração produz a próxima:
- **Seleção por rank**: ordenamos a população por fitness e damos mais chance aos melhores. Usamos
  *rank* (posição) e não `1/fitness` porque as multas geram valores gigantes que quebrariam a
  proporção direta.
- **Elitismo**: o **melhor** indivíduo de cada geração é copiado intacto, para nunca regredir.
- **Crossover OX (Order Crossover)**: combina dois pais preservando **cada cliente exatamente uma
  vez** — nenhum ponto de entrega é duplicado ou esquecido.
- **Mutação**: com certa probabilidade aplica **um** de três operadores — **swap** (troca dois),
  **inversion** (inverte um trecho) ou **reallocate** (move um cliente de lugar) — para manter
  diversidade e escapar de ótimos locais.

🖥️ Bloco do loop em `tsp.py` (seleção → OX → mutate) + mini-diagramas de cada operador.

---

## ⏱️ [7:45–9:30] DEMO AO VIVO

🖥️ Rodar:

```bash
.venv/Scripts/python.exe tsp.py
```

🎙️ Narrar em tempo real, amarrando cada elemento da tela aos conceitos já explicados:
1. **Gráfico de convergência** (esquerda): a curva de custo **caindo** geração a geração = a
   evolução está funcionando.
2. **Mapa** (centro): o **hospital** central (quadrado vermelho com cruz), os pontos **críticos**
   destacados, e as **rotas coloridas** (uma cor por veículo, com setas de direção) "desembaraçando".
3. **Dashboard** (direita): carga e distância de cada veículo **vs. os limites**, e os alertas
   mudando de vermelho ("SOBRECARGA"/"AUTONOMIA EXCEDIDA") para **"OK"** conforme as rotas viram
   viáveis.
4. **Console**: a linha `Geração N: Melhor Custo = ...` acompanhando o gráfico.

---

## ⏱️ [9:30–10:00] Fechamento

🎙️ Recapitular os **4 ingredientes** e o resultado: o algoritmo encontra **rotas viáveis** que
respeitam carga e autonomia e **priorizam o urgente**, sem que ninguém precise programar a solução
manualmente. Citar **extensões** possíveis: janelas de tempo, frotas maiores, instâncias maiores
(como o benchmark `att48`). Agradecer / créditos.

🖥️ Slide-resumo + tela final da demo já convergida.

---

## 📋 Notas de produção / checklist de gravação

- **Ensaie a demo antes**: rode `.venv/Scripts/python.exe tsp.py` e deixe convergir uma vez para
  saber quanto tempo leva até estabilizar; ajuste a narração do bloco de demo conforme.
- **Demo mais limpa (opcional)**: em `tsp.py`, dá para usar uma instância fixa descomentando
  `default_problems[15]` no lugar da geração aleatória — **apenas para a gravação, não commitar**.
- **Legibilidade**: a janela é 1200×500; grave em resolução que deixe o dashboard à direita legível.
- **Overlays de código a ter à mão**: dataclasses `City`/`FleetConfig`, `split_routes`, docstring de
  `calculate_fitness`, e o bloco de seleção/crossover/mutação do `tsp.py`.
- **Ajuste de duração**: a soma dá ~10 min. Para 8 min, encurte o bloco [2:00–3:15]; para 12 min,
  estenda a demo ao vivo.

## ✅ Conferência de fidelidade ao código

- Representação por **IDs de cidades** (depósito = 0, fora do cromossomo). ✔ `genetic_algorithm.py`
- `split_routes` **guloso** por capacidade/autonomia. ✔ `genetic_algorithm.py`
- Termos e pesos do fitness (×1000 capacidade/autonomia, ×5000 frota). ✔ `calculate_fitness`
- **Seleção por rank** + **elitismo**. ✔ `tsp.py`
- **OX** + três mutadores (**swap/inversion/reallocate**). ✔ `order_crossover`, `mutate`
- Três painéis na visualização (convergência, mapa, dashboard). ✔ `draw_functions.py`
