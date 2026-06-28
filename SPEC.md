# Especificação Técnica: Sistema de Otimização de Rotas de Entrega Hospitalar (VRP)

Esta especificação orienta o desenvolvimento e a transição do atual solucionador de Caixeiro Viajante (TSP) para um sistema de **Roteamento de Veículos (VRP)** com restrições do mundo real no contexto hospitalar (entrega de medicamentos e insumos).

---

## 1. Arquitetura do Sistema e Representação Genética

### 1.1. Representação Genética (Cromossomo)
O cromossomo deve ser capaz de codificar rotas para múltiplos veículos que partem e retornam ao mesmo depósito central (Hospital/Depósito).
*   **Abordagem Recomendada (Delimitadores):** Uma única sequência contendo todas as cidades (clientes) e delimitadores especiais representados por IDs de veículos ou valores específicos (ex: `0` para o depósito).
    *   *Exemplo:* Para as cidades de `1` a `6` e `3` veículos, uma rota como `[0, 1, 3, 0, 2, 5, 0, 4, 6, 0]` indica:
        *   Veículo 1: Hospital (0) $\rightarrow$ 1 $\rightarrow$ 3 $\rightarrow$ Hospital (0)
        *   Veículo 2: Hospital (0) $\rightarrow$ 2 $\rightarrow$ 5 $\rightarrow$ Hospital (0)
        *   Veículo 3: Hospital (0) $\rightarrow$ 4 $\rightarrow$ 6 $\rightarrow$ Hospital (0)
*   **Abordagem Alternativa (Estrutura de Duas Partes):**
    *   Uma lista contendo a permutação dos clientes visitados.
    *   Uma segunda lista ou vetor que define os pontos de corte/divisão para cada veículo.

### 1.2. Operadores Genéticos Especializados
Os operadores de crossover e mutação padrão do TSP precisam ser adaptados para respeitar a estrutura de múltiplos veículos sem duplicar ou omitir clientes:
*   **Seleção:** Torneio ou Roleta (proporcional ao fitness).
*   **Crossover (Cruzamento):**
    *   *Order Crossover (OX) Modificado:* Preserva a ordem relativa de visitas às cidades, reavaliando os pontos de corte e partição dos veículos.
*   **Mutação:**
    *   *Swap Mutator:* Troca a posição de duas cidades (mesmo que estejam em rotas de veículos diferentes).
    *   *Inversion Mutator:* Inverte um trecho da rota (sub-rota).
    *   *Reallocate Mutator:* Move uma cidade da rota de um veículo para a de outro.

---

## 2. Modelagem das Restrições e Função Fitness

A função de aptidão (*fitness*) deve ir além da mera distância euclidiana, incorporando penalidades para restrições violadas.

### 2.1. Variáveis das Cidades/Clientes
Cada destino de entrega $i$ deve possuir atributos adicionais:
1.  **Demanda ($q_i$):** Peso ou volume da carga a ser entregue (em kg ou unidades).
2.  **Prioridade ($P_i$):** Nível de urgência da entrega:
    *   *Medicamentos Críticos (Urgente):* Alta prioridade (ex: peso multiplicador elevado).
    *   *Insumos Regulares:* Prioridade padrão.

### 2.2. Restrições Realistas
1.  **Capacidade de Carga dos Veículos ($Q_{max}$):**
    *   A soma das demandas de todas as cidades em qualquer rota individual de um veículo não deve exceder $Q_{max}$.
    *   $\sum_{i \in \text{Rota}_k} q_i \le Q_{max}, \quad \forall k$.
2.  **Autonomia Limitada ($D_{max}$):**
    *   A distância total percorrida por qualquer veículo individualmente não deve exceder a autonomia máxima $D_{max}$ (limite de combustível/bateria).
    *   $\text{Distancia}(\text{Rota}_k) \le D_{max}, \quad \forall k$.
3.  **Múltiplos Veículos ($V$):**
    *   Limite fixo no número de veículos disponíveis na frota.

### 2.3. Função Fitness com Penalização
O objetivo é **minimizar** o custo total. O fitness deve refletir:
$$\text{Custo Total} = \sum_{k=1}^{V} \text{Distancia}(\text{Rota}_k) + \sum_{i \in \text{Cidades}} \text{PenalidadePrioridade}(i) + \text{PenalidadesRestrições}$$

Onde:
*   **Penalidade de Prioridade:** Adiciona um custo adicional se entregas de alta prioridade forem postergadas (realizadas no final da rota de um veículo em vez do início).
    *   *Fórmula sugerida:* $P_i \times \text{Tempo de Espera até o cliente } i$.
*   **Penalidades de Restrições:** Caso uma rota exceda a capacidade $Q_{max}$ ou autonomia $D_{max}$, aplica-se uma grande penalidade proporcional ao excesso.

---

## 3. Visualização e Interface Gráfica

A visualização em Pygame deve ser estendida para suportar múltiplos veículos:
*   **Diferenciação de Rotas:** Desenhar cada rota de veículo com uma cor única (ex: Rota 1 = Azul, Rota 2 = Verde, Rota 3 = Laranja).
*   **Indicação visual das cidades:**
    *   Depósito/Hospital desenhado com destaque (ex: quadrado vermelho ou ícone de H).
    *   Cidades com Medicamentos Críticos (alta prioridade) desenhadas com tamanho ou cor diferente (ex: círculos vermelhos pulsantes).
    *   Cidades com insumos regulares em cor padrão (ex: círculos pretos/azuis).
*   **Painel Informativo lateral/inferior:**
    *   Gráfico de convergência do fitness do Matplotlib à esquerda (mantido do código base).
    *   Estatísticas de cada veículo (carga atual vs capacidade, distância percorrida vs autonomia).
    *   Status global (Total de veículos em uso, distância total somada, penalidades ativas).

---

## 4. Plano de Implementação Sugerido

### Passo 1: Refatoração do Modelo de Dados
*   Criar uma classe `City` ou estender a estrutura para incluir coordenadas, demanda de carga e nível de prioridade.
*   Definir os parâmetros globais da frota: `NUM_VEHICLES`, `VEHICLE_CAPACITY`, `VEHICLE_AUTONOMY`.

### Passo 2: Adaptação do Algoritmo Genético (`genetic_algorithm.py`)
*   Atualizar `generate_random_population` para gerar cromossomos válidos para VRP.
*    Reescrever `calculate_fitness` para calcular distâncias por rota individual de veículo, aplicar penalidades de capacidade, autonomia e urgência (prioridades).
*   Atualizar os operadores de mutação e crossover para manipular corretamente a nova estrutura de rotas.

### Passo 3: Atualização do Loop de Simulação e Renderização (`tsp.py` e `draw_functions.py`)
*   Modificar as funções de desenho em `draw_functions.py` para receber as rotas segmentadas por veículo.
*   Associar uma cor a cada veículo e desenhar as linhas conectando as cidades de cada rota de volta ao hospital.
*   Exibir na tela do Pygame o status detalhado da frota em tempo real.

---

## 5. Critérios de Aceitação e Verificação

1.  **Ausência de Colisões de Capacidade/Autonomia:** O algoritmo deve convergir para rotas que respeitam os limites de carga e distância máxima, ou exibir claramente no console/tela as infrações residuais.
2.  **Urgência Respeitada:** Clientes classificados como "Medicamento Crítico" devem tender a aparecer no início de suas respectivas rotas para minimizar o atraso.
3.  **Visualização Clara:** A janela do Pygame deve mostrar claramente as rotas de cada veículo com cores distintas e a legenda indicando a carga de cada um.
