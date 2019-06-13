# if you want to import a model you need to keep in under the db instance, because it won't know until then
# need to treat the rest of the blog like a package 
from flask import Flask, render_template, send_from_directory, send_file, url_for, flash, redirect, request
from gene_wizard import app, mysql
#from gene_wizard.forms import 
#from gene_wizard.models import 


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

@app.route('/gProfilerTest')
def gProfilerTest():

    conn = mysql.connect()
    cursor = conn.cursor()
    try: 
        cursor.execute("SELECT DISTINCT e.ENSG_id FROM DEG_lncRNA_roster d, Expression e WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id AND d.lncRNA_name = 'MANCR' AND e.log2FoldChange < 0;") 
        genes_down = cursor.fetchall()
        
        cursor.execute("SELECT DISTINCT e.gene_symbol FROM DEG_lncRNA_roster d, Expression e WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id AND d.lncRNA_name = 'MANCR' AND e.log2FoldChange > 0;") 
        genes_up = cursor.fetchall()
        
    finally: 
        cursor.close()

    return render_template('gProfilerTest.html', genes_down=genes_down, genes_up=genes_up)

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

@app.route("/Data", methods=['GET', 'POST']) 
def results():
    form = LoginForm()
    if form.validate_on_submit():

        if form.email.data == 'admin@blog.com' and form.password.data == 'password':
            flash('you have been logged in!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')

    return render_template('login.html', title = 'Login', form=form)
    