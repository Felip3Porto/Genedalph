# if you want to import a model you need to keep in under the db instance, because it won't know until then
# need to treat the rest of gene_wizard like a package 
from flask import Flask, render_template, send_from_directory, send_file, url_for, flash, redirect, request, Markup
from gene_wizard import app, mysql

# use a custom agent of the Gprofiler API
from gprofiler import GProfiler
gp = GProfiler(
    user_agent='Genedalph', #thanks Uku
    return_dataframe=True, #return pandas dataframe or plain python structures    
)
# for the graphing to be sent
import math
import plotly.graph_objs as go
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import pandas as pd

#because they are in the package now ya gotta have the dot before your own created objects

@app.route("/", methods=['GET', 'POST'])#root or homepage
@app.route("/home") 
def home():

    if request.method == 'POST':
        #Fetch form data 
        DEG_lncRNA_roster = request.form 
        lncRNA_name = DEG_lncRNA_roster['lncRNA_name']
        lncRNA_name = lncRNA_name.replace(';','')

        # cell_line = DEG_lncRNA_roster['cell_line']

        #make a cursor to use 
        cursor = mysql.connect().cursor()
        # cursor.execute("SELECT e.ENSG_id, e.gene_symbol, e.baseMean, e.log2FoldChange, e.lfcSE, e.pvalue, e.stat, e.padj")
        # cursor.execute("FROM Expression e, DEG_lncRNA_roster d")
        # cursor.execute("WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id and d.lncRNA_name = " + lncRNA_name + ";")
        try: 
            cursor.execute("SELECT e.ENSG_id, e.gene_symbol, e.baseMean, e.log2FoldChange, e.lfcSE, e.pvalue, e.stat, e.padj FROM Expression e, DEG_lncRNA_roster d WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id and d.lncRNA_name = '" + lncRNA_name + "';")
            expression_data = cursor.fetchall()
            #2
            cursor.execute("SELECT DISTINCT g.path_to_plot  FROM Expression e, DEG_lncRNA_roster d, PreRanking p, GSEA_reports g WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id  AND d.lncRNA_name = '"+ lncRNA_name +"'  AND e.DEG_lncRNA_roster_roster_id = p.Expression_expression_id  AND p.prerank_id = g.PreRanking_prerank_id AND g.path_to_plot IS NOT NULL AND g.path_to_plot LIKE '%_up_%' AND g.path_to_plot NOT LIKE '%_down_%' ORDER BY g.fdr ASC;") 
            graphs_up_reg = cursor.fetchall()
            #3 
            cursor.execute("SELECT DISTINCT g.path_to_plot  FROM Expression e, DEG_lncRNA_roster d, PreRanking p, GSEA_reports g WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id  AND d.lncRNA_name = '"+ lncRNA_name +"'  AND e.DEG_lncRNA_roster_roster_id = p.Expression_expression_id  AND p.prerank_id = g.PreRanking_prerank_id AND g.path_to_plot IS NOT NULL AND g.path_to_plot LIKE '%_down_%' AND g.path_to_plot NOT LIKE '%_up_%' ORDER BY g.fdr ASC;") 
            graphs_down_reg = cursor.fetchall()
        finally:
            cursor.close()
        # cursor.execute("SELECT * FROM DEG_lncRNA_roster WHERE lncRNA_name='" + lncRNA_name + "'")
            data = cursor.fetchall()
        # cursor.execute("INSERT INTO search2(lncRNA_name) VALUES(%s)", lncRNA_name)
        # .commit seems to be for inserting only
        
        if data is None:
            return "That lncRNA is not available in genedalf"
        else:
            return render_template('test.html', expression_data=expression_data, graphs_up_reg=graphs_up_reg, graphs_down_reg=graphs_down_reg, lncRNA_name=lncRNA_name)
            # return redirect('/results', expression_data=expression_data, graphs_up_reg=graphs_up_reg, graphs_down_reg=graphs_down_reg)
            # returning just data is not possible 
            # send to appropriate routes  

        cursor.close()

    return render_template('home.html') 
    # that posts = posts bit allows the html to reference our data inside here 
    # also remember that flask checks for a folder called templates

# @app.route("/about") 
# def about():
#     return render_template('about.html', title = 'About')

@app.route('/gProfilerTest', methods=['GET', 'POST'])
def gProfilerTest():

    conn = mysql.connect()
    cursor = conn.cursor()
    try: 
        cursor.execute("SELECT DISTINCT e.ENSG_id FROM DEG_lncRNA_roster d, Expression e WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id AND d.lncRNA_name = 'MANCR' AND e.log2FoldChange < 0;") 
        genes_down = cursor.fetchall()
        query_down=[i[0] for i in genes_down]
        # seems like genes_down etc are very large even on the API side to handle
        # makina a stringent separate query can get the most graph possible 
        cursor.execute("SELECT DISTINCT e.gene_symbol FROM DEG_lncRNA_roster d, Expression e WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id AND d.lncRNA_name = 'MANCR' AND e.log2FoldChange > 0;") 
        genes_up = cursor.fetchall()
        # needs to be done before the cursor close
        # cursor object is not like a list at all 
        query_up=[i[0] for i in genes_up]
        
    finally: 
        cursor.close()
    print(query_down)
    print(type(query_down))
    print(len(query_down))
    #query the upregulated and downregulated genes 
    sources = ["GO:MF","GO:CC","GO:BP","KEGG","REAC","WP"]
    # tricky cursor needs to be put in a python list 

    # GET dataframes of pathways 
    
    # GOSTup = gp.profile(organism='hsapiens', query = query_up, sources = sources, no_evidences=False) 
    # GOSTdown = gp.profile(organism='hsapiens', query = query_down, sources = sources, no_evidences=False) 
    # get lists for plotting 
    # 3 things GOids, -log(adjP), and terms
    # xGOtermsUp = GOSTup.native.to_list()
    # # remember that pval is already corrected and the bar is -log(padj)
    # listPadjUp = GOSTup.p_value.to_list()
    # yPadjUp = []
    # for e in listPadjUp:
    #     yPadjUp.append(-math.log(e))
    # GOtextUp = GOSTup.name.to_list()
    # xGOtermsDown = GOSTdown.native.to_list()
    # listPadjDown = GOSTdown.p_value.to_list()
    # yPadjDown = []
    # for i in listPadjDown:
    #     yPadjDown.append(-math.log(i))
    # GOtextDown = GOSTdown.name.to_list()
        
    # since it is a dict cursor try sending the df as a dict or json
    return render_template('gProfilerTest.html', genes_down=genes_down, genes_up=genes_up) #, jsonify(result={"status": 200})

@app.route('/test')
def test():
    conn = mysql.connect()
    cursor =conn.cursor()
   
    try:
        #1 
        cursor.execute("SELECT e.ENSG_id, e.gene_symbol, e.baseMean, e.log2FoldChange, e.lfcSE, e.pvalue, e.stat, e.padj FROM Expression e, DEG_lncRNA_roster d WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id and d.lncRNA_name = 'MANCR';")
        expression_data = cursor.fetchall()
        #2
        cursor.execute("SELECT DISTINCT g.path_to_plot  FROM Expression e, DEG_lncRNA_roster d, PreRanking p, GSEA_reports g WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id  AND d.lncRNA_name = 'MANCR'  AND e.DEG_lncRNA_roster_roster_id = p.Expression_expression_id  AND p.prerank_id = g.PreRanking_prerank_id AND g.path_to_plot IS NOT NULL AND g.path_to_plot LIKE '%_up_%' AND g.path_to_plot NOT LIKE '%_down_%' ORDER BY g.fdr DESC;") 
        graphs_up_reg = cursor.fetchall()
        #3 
        cursor.execute("SELECT DISTINCT g.path_to_plot  FROM Expression e, DEG_lncRNA_roster d, PreRanking p, GSEA_reports g WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id  AND d.lncRNA_name = 'MANCR'  AND e.DEG_lncRNA_roster_roster_id = p.Expression_expression_id  AND p.prerank_id = g.PreRanking_prerank_id AND g.path_to_plot IS NOT NULL AND g.path_to_plot LIKE '%_down_%' AND g.path_to_plot NOT LIKE '%_up_%' ORDER BY g.fdr DESC;") 
        graphs_down_reg = cursor.fetchall()
    
    finally: 
        cursor.close()
    image_name = url_for("Data/Reports/SENCR_up_report/positive regulation of transferase activity (GO_0051347).prerank.png")
    return render_template('test.html', expression_data=expression_data, graphs_up_reg=graphs_up_reg, graphs_down_reg=graphs_down_reg, image_name=image_name)

@app.route("/report/<filename>")
def send_image(filename):
    # filename = url_for(filename)
    return send_file(filename, mimetype='image/png')
    # return send_from_directory("Data" , filename)
    