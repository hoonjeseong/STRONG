include: "Common.snake"

configfile: "config.yaml"

rule all: 
   input:expand("annotation/{group}/{group}_SCG.bed", group=GROUPS)

#find for ORFs
rule prodigal:
    input:"assembly/%s/{group}.fasta" % ASSEMBLER
    output:
        faa="annotation/{group}/{group}.faa",
        fna="annotation/{group}/{group}.fna",
        gff="annotation/{group}/{group}.gff"
    log: 
        "annotation/{group}/prodigal.log" 
    shell:
        "prodigal -i {input} -a {output.faa} -d {output.fna} -f gff -p meta -o {output.gff} &> {log} "


#Cut faa file in chunks, so that we can have faster annotation  
rule split_fasta:
    input:
        "annotation/{group}/{group}.faa"
    output:
        touch("annotation/{group}/temp_splits/folder.done")
    threads:
        THREADS
    shell:
        "Fasta_Batchs.py {input} {threads} -t annotation/{wildcards.group}/temp_splits/" 


#Do rpsblast annotation  
rule rpsblast_on_folder:
    input:
        name="annotation/{group}/{filename}.faa",
        touch="annotation/{group}/temp_splits/folder.done"
    output:
        "annotation/{group}/{filename}_Rpsblast_cogs.tsv"
    log:
        "annotation/{group}/{filename}_Rpsblast.log"
    threads:
        THREADS
    shell:
        """
        Rpsblast_loop.sh annotation/{wildcards.group}/temp_splits {threads} &>log
        mv annotation/{wildcards.group}/temp_splits/Complete_Rpsblast_cogs.tsv {output}
        """

# select best hit and use criterion : min 5% coverage, min 1e-10 evalue
rule parse_cogs_annotation:
    input:
        "annotation/{group}/{filename}_Rpsblast_cogs.tsv"    
    output:
        "annotation/{group}/{filename}_Cogs_filtered.tsv"
    shell:
        "Filter_Cogs.py {input} --cdd_cog_file /home/sebr/seb/Applications/CONCOCT/scgs/cdd_to_cog.tsv  > {output}"

# transform gff into bed  
rule gff_to_bed:
    input:
        "annotation/{group}/{group}.gff"
    output:
        "annotation/{group}/{group}.bed2"
    shell:
        "Gff_to_bed.py {input}"


# extract from the bed file all position of SCG 
rule build_SCG_bed:
    input:
        annotation="annotation/{group}/{filename}_Cogs_filtered.tsv",
        bed="annotation/{group}/{group}.bed2"
    output:
        "annotation/{group}/{filename}_SCG.bed"
    shell:
        "Extract_SCG.py {input.bed} {input.annotation} /home/sebr/seb/Applications/CONCOCT/scgs/scg_cogs_min0.97_max1.03_unique_genera.txt>{output}"

