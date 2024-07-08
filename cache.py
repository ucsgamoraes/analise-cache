import configparser
import random
import json
import math
import os

#constantes
address_size = 32

#I/O
file_name = "oficial.cache"
config_file = "config.ini"

#estado
leituras_memoria = 0
escritas_memorias = 0
enderecos_escritas = 0
enderecos_leituras = 0
hit_count_leitura = 0
hit_count_escrita = 0

cache1 = None

#setar parametros com o arquivo de configuracao
config = configparser.ConfigParser()
config.read(config_file)

cache_config = config['CacheConfig']

#parametros
write_policy = cache_config.get('write_policy', 'wb')
substitution_policy = cache_config.get('substitution_policy', 'lfu')
line_size = int(cache_config.get('line_size'))
associativity = int(cache_config.get('associativity'))
line_count = int(cache_config.get('line_count'))
hit_access_time = int(cache_config.get('hit_access_time'))
mm_access_time = int(cache_config.get('mm_access_time'))
write_miss_policy = cache_config.get('write_miss_policy', 'wa')
output_file_path = cache_config.get('output_file_path', 'output.txt')
graph_file_path = cache_config.get('graph_file_path', '')

class Block:
    def __init__ (self, tag, dirty):
        self.tag = tag
        self.dirty = dirty 
        self.lru = 0 
        self.lfu = 0 
class Set:
    def __init__ (self, blocks_per_set):
        self.blocks = [Block(-1, 0) for _ in range(blocks_per_set)]

class Cache:
    def __init__ (self, blocks_per_set, set_number):
        self.blocks_per_set = blocks_per_set
        self.sets = [Set(blocks_per_set) for _ in range(set_number)]

def main ():
    global line_count, associativity, cache1, enderecos_escritas, enderecos_leituras, write_policy, line_size, mm_access_time, substitution_policy

    #cria cache com os parametros
    conjuntos_numero = int(line_count/associativity)
    cache1 = Cache(associativity, conjuntos_numero)

    #le arquivo e faz as operacoes
    operations_file = open(file_name, "r")
    while True:
        line_data = operations_file.readline()
        if line_data == '':
            break
        instruction, operation = line_data.split()
        set_index, block_tag = decode_instruction(instruction)
        execute_operation(set_index, block_tag, operation) 

    escreve_resultado()

def escreve_resultado ():   
    f = open(output_file_path, "w+", encoding="utf-8")

    f.write(f"Política de substituição: {substitution_policy }\n")
    f.write(f"Tamanho da linha: {line_size}\n")
    f.write(f"Associatividade: {associativity}\n")
    f.write(f"Quantidade de linhas: {line_count}\n")
    f.write(f"Tempo de acesso em caso de acerto: {hit_access_time}ns\n")
    f.write(f"Tempo de acesso à memória principal: {mm_access_time}ns\n")
    f.write(f"Tamanho da cache (bytes): {line_size*line_count}\n")

    if write_policy == 'wb':
        f.write("Política de escrita: write-back\n")
    elif write_policy == 'wt':
        f.write("Política de escrita: write-trought\n")

    f.write(f"Endereços de escrita: {enderecos_escritas}\n")
    f.write(f"Endereços de leitura: {enderecos_leituras}\n")
    f.write(f"Endereços de leitura + escrita: {enderecos_leituras + enderecos_escritas}\n")
    f.write(f"Acessos a memoria principal: {escritas_memorias+leituras_memoria}\n")
    f.write(f"Escritas a memoria principal: {escritas_memorias}\n")
    f.write(f"Leituras a memoria principal: {leituras_memoria}\n")

    taxa_hit_leitura = hit_count_leitura/enderecos_leituras 
    taxa_hit_escrita = hit_count_escrita/enderecos_escritas
    taxa_hit_global = (hit_count_escrita+hit_count_leitura)/(enderecos_escritas+enderecos_leituras)
    tempo_medio = taxa_hit_global * hit_access_time + (1 - taxa_hit_global) * (hit_access_time + mm_access_time)
    tempo_medio = round(tempo_medio, 4)

    taxa_hit_escrita = round(taxa_hit_escrita*100, 4)
    taxa_hit_leitura = round(taxa_hit_leitura*100, 4)
    taxa_hit_global = round(taxa_hit_global*100, 4)
    
    f.write(f"Taxa de hit (leitura) : {taxa_hit_leitura}% ({hit_count_leitura})\n")
    f.write(f"Taxa de hit (escrita) : {taxa_hit_escrita}% ({hit_count_escrita})\n")
    f.write(f"Taxa de hit (global) : {taxa_hit_global}% ({hit_count_escrita+hit_count_leitura})\n")
    f.write(f"Tempo médio: {tempo_medio}ns\n")

    if graph_file_path:
        data = {
            "taxa_hit_leitura_values": [],
            "taxa_hit_escrita_values": [],
            "taxa_hit_global_values": [],
            "tempo_medio_values": [],
            "tamanho_linha": [],
            "associatividade": [],
            "quantidade_blocos": [],
        }
        if os.path.exists(graph_file_path):
            with open(graph_file_path, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)

        data["taxa_hit_leitura_values"].append(taxa_hit_leitura)
        data["taxa_hit_escrita_values"].append(taxa_hit_escrita)
        data["taxa_hit_global_values"].append(taxa_hit_global)
        data["tempo_medio_values"].append(tempo_medio)
        data["tamanho_linha"].append(line_size)
        data["associatividade"].append(associativity)
        data["quantidade_blocos"].append(line_count)

        with open(graph_file_path, "w+", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

    f.close()

def read_operation (set_index, block_tag):
    global escritas_memorias, leituras_memoria, enderecos_escritas, hit_count_leitura 
    current_block = 0
    capacity_miss = 1 
    current_set = cache1.sets[set_index]

    for block in current_set.blocks:
        if block.tag == block_tag: #hit
            capacity_miss = 0
            current_block = block
            hit_count_leitura += 1
            break
        elif block.tag == -1: #miss
            block.tag = block_tag
            #ler mm
            leituras_memoria += 1
            block.dirty = 0
            capacity_miss = 0
            current_block = block
            break

    if capacity_miss:
        #selecionar bloco para substituir
        if substitution_policy == 'aleatorio':
            random_index = random.randrange(0, cache1.blocks_per_set)        
            current_block = current_set.blocks[random_index]
        elif substitution_policy == 'lru':
            lru_block = max(current_set.blocks, key=lambda b: b.lru)
            current_block = lru_block 
        elif substitution_policy == 'lfu':
            lfu_block = min(current_set.blocks, key=lambda b: b.lfu)
            lfu_block.lfu = 0 
            current_block = lfu_block 

        if write_policy == 'wb':
            #escreve bloco escolhido na memoria
            if current_block.dirty:
                #escreve mm
                escritas_memorias += 1
            #busca dados do bloco para ler na memoria
            leituras_memoria += 1
            #escreve bloco na cache
            current_block.tag = block_tag
            current_block.dirty = 0 
        elif write_policy == 'wt':
            #escreve na memoria e na cache
            leituras_memoria += 1
            current_block.tag = block_tag

    #atualizar
    if substitution_policy == 'lru':
        for block in current_set.blocks:
            block.lru += 1
        current_block.lru = 0
    elif substitution_policy == 'lfu':
        current_block.lfu += 1 

def write_operation (set_index, block_tag):
    global escritas_memorias, hit_count_escrita, leituras_memoria
    #pesquisa bloco
    current_set = cache1.sets[set_index]
    capacity_miss = 1
    current_block = None
    hit = 0

    for block in current_set.blocks:
        # (cache hit)
        if block.tag == block_tag:
            #escreve so na cache e seta o dirty bit
            if write_policy == 'wb':
                block.dirty = 1
            #escreve na memoria e na cache
            elif write_policy == 'wt':
                escritas_memorias += 1 
            hit_count_escrita += 1
            current_block = block
            hit = 1
            break
        elif block.tag == -1:
            current_block = block
            capacity_miss = 0
            break
            
    if not hit:
        if write_miss_policy == 'wa':
            # traz bloco da memoria principal
            leituras_memoria += 1
            #selecionar bloco para substituir
            if capacity_miss:
                if substitution_policy == 'aleatorio':
                    random_index = random.randrange(0, cache1.blocks_per_set)        
                    current_block = current_set.blocks[random_index]
                elif substitution_policy == 'lru':
                    lru_block = max(current_set.blocks, key=lambda b: b.lru)
                    current_block = lru_block 
                elif substitution_policy == 'lfu':
                    lfu_block = min(current_set.blocks, key=lambda b: b.lfu)
                    lfu_block.lfu = 0 
                    current_block = lfu_block 
                #escrever bloco na memoria 
                if write_miss_policy == 'wb' and current_block.dirty:
                    escritas_memorias += 1
            #escreve so na cache e seta dirty bit
            if write_policy == 'wb':
                current_block.tag = block_tag
                current_block.dirty = 0 
            #escreve na cache o bloco que foi trazido
            elif write_policy == 'wt':
                escritas_memorias += 1
                current_block.tag = block_tag
        elif write_miss_policy == 'wna':
            #escreve so na mm
            escritas_memorias += 1
        #atualizar
    if substitution_policy == 'lru':
        for block in current_set.blocks:
            block.lru += 1
        current_block.lru = 0
    elif substitution_policy == 'lfu':
        current_block.lfu += 1 
 
def execute_operation(set_index, block_tag, operation):
    global enderecos_escritas, enderecos_leituras
    if operation == 'R':
        enderecos_leituras += 1
        read_operation(set_index, block_tag) 
    elif operation == 'W':
        enderecos_escritas += 1
        write_operation(set_index, block_tag)

def decode_instruction (instruction):
    instruction_int = int(instruction, 16)
    instruction_bin = format(instruction_int, '032b')

    palavra_bits = int(math.log2(line_size))
    conjuntos_qnt = line_count/associativity;
    conjunto_bits = int(math.log2(conjuntos_qnt))
    rotulo_bits = address_size - (conjunto_bits + palavra_bits)

    conjunto = instruction_bin[rotulo_bits:(rotulo_bits+conjunto_bits)]
    conjunto = conjunto if conjunto else '0'
    rotulo = instruction_bin[:rotulo_bits]
    return int(conjunto, 2) , int(rotulo, 2)     

main()