/* 
    1. Have a table which displays the expression that that belongs to a specific lncRNA 
    2. Order the graphs(paths) for decending order (highest to lowest fdr) for up regulated 
    3. Order the graphs(paths) for decending order (highest to lowest fdr) for up regulated 
    4. Table which has all of the preRankReport information for up regulated and down regulated genes  
*/
-- 1. d.lncRNA_name will be where a stripped query will go  
SELECT e.ENSG_id, e.gene_symbol, e.baseMean, e.log2FoldChange, e.lfcSE, e.pvalue, e.stat, e.padj
FROM Expression e, DEG_lncRNA_roster d
WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id and d.lncRNA_name = "MANCR"; 

-- 2. 
SELECT DISTINCT g.path_to_plot 
FROM Expression e, DEG_lncRNA_roster d, PreRanking p, GSEA_reports g
WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id 
AND d.lncRNA_name = "MANCR" 
AND e.DEG_lncRNA_roster_roster_id = p.Expression_expression_id 
AND p.prerank_id = g.PreRanking_prerank_id
AND g.path_to_plot IS NOT NULL
AND g.path_to_plot LIKE '%_up_%'
AND g.path_to_plot NOT LIKE '%_down_%'
ORDER BY g.fdr DESC; -- OR 

-- SELECT g.Term, p.prerank_id, e.DEG_lncRNA_roster_roster_id, d.lncRNA_name
-- FROM GSEA_reports g 
-- LEFT JOIN PreRanking p ON p.prerank_id = g.PreRanking_prerank_id
-- LEFT JOIN Expression e ON e.expression_id = p.Expression_expression_id ------ rith
-- LEFT JOIN DEG_lncRNA_roster d ON d.roster_id = e.DEG_lncRNA_roster_roster_id;

-- ---moment of truth found bug 
-- SELECT g.Term, d.lncRNA_name
-- FROM GSEA_reports g 
-- LEFT JOIN PreRanking p ON p.prerank_id = g.PreRanking_prerank_id
-- LEFT JOIN Expression e ON e.DEG_lncRNA_roster_roster_id = p.Expression_expression_id 
-- LEFT JOIN DEG_lncRNA_roster d ON d.roster_id = e.DEG_lncRNA_roster_roster_id;

-- 2 
-- try inner to remove duplicates 
SELECT DISTINCT g.path_to_plot 
FROM GSEA_reports g 
INNER JOIN PreRanking p ON p.prerank_id = g.PreRanking_prerank_id
INNER JOIN Expression e ON e.DEG_lncRNA_roster_roster_id = p.Expression_expression_id 
INNER JOIN DEG_lncRNA_roster d ON d.roster_id = e.DEG_lncRNA_roster_roster_id
WHERE d.lncRNA_name = "MANCR"
AND e.log2FoldChange < 0 
ORDER BY g.fdr DESC;

-- 3 a bit bodge but we can fix later and it works
SELECT DISTINCT g.path_to_plot 
FROM Expression e, DEG_lncRNA_roster d, PreRanking p, GSEA_reports g
WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id 
AND d.lncRNA_name = "MANCR" 
AND e.DEG_lncRNA_roster_roster_id = p.Expression_expression_id 
AND p.prerank_id = g.PreRanking_prerank_id
AND g.path_to_plot IS NOT NULL
AND g.path_to_plot LIKE '%_down_%'
AND g.path_to_plot NOT LIKE '%_up_%'
ORDER BY g.fdr DESC; 

-- 4 

-- SELECT DISTINCT g.Term, g.es, g.nes, g.pval, g.fdr, g.geneset_size, g.matched_size
-- FROM GSEA_reports g 
-- INNER JOIN PreRanking p ON p.prerank_id = g.PreRanking_prerank_id
-- INNER JOIN Expression e ON e.DEG_lncRNA_roster_roster_id = p.Expression_expression_id 
-- INNER JOIN DEG_lncRNA_roster d ON d.roster_id = e.DEG_lncRNA_roster_roster_id
-- WHERE d.lncRNA_name = "MANCR"
-- AND e.log2FoldChange < 0 
-- ORDER BY g.fdr DESC;
SELECT DISTINCT p.path_to_prerank
FROM PreRanking p
INNER JOIN GSEA_reports g ON p.prerank_id = g.PreRanking_prerank_id
INNER JOIN Expression e ON e.DEG_lncRNA_roster_roster_id = p.Expression_expression_id 
INNER JOIN DEG_lncRNA_roster d ON d.roster_id = e.DEG_lncRNA_roster_roster_id
WHERE d.lncRNA_name = "MANCR"
AND p.path_to_prerank LIKE '%_up_%'
AND p.path_to_prerank NOT LIKE '%_down_%';

SELECT DISTINCT p.path_to_prerank
FROM PreRanking p
INNER JOIN GSEA_reports g ON p.prerank_id = g.PreRanking_prerank_id
INNER JOIN Expression e ON e.DEG_lncRNA_roster_roster_id = p.Expression_expression_id 
INNER JOIN DEG_lncRNA_roster d ON d.roster_id = e.DEG_lncRNA_roster_roster_id
WHERE d.lncRNA_name = "MANCR"
AND p.path_to_prerank LIKE '%_down_%'
AND p.path_to_prerank NOT LIKE '%_up_%';


-- select s.firstname, s.lastname 
-- from Student s, AssistAssignment a 
-- where a.studentID = s.studentID and a.assistType = 'TA' and a.assistType = 'RA'; 
