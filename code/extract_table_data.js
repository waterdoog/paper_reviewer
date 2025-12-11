// 在浏览器控制台运行此脚本来提取所有 forum ID 和表格数据
// Run this script in browser console to extract all forum IDs and table data
// 使用方法：打开 https://agents4science.stanford.edu/submissions.html，按 F12 打开控制台，粘贴此脚本并运行
// Usage: Open https://agents4science.stanford.edu/submissions.html, press F12 to open console, paste this script and run
// 
// 输出格式 / Output format:
// {
//   "forum_id_1": {
//     "title": "...",
//     "status": "...",
//     "primary_topic": "...",
//     "secondary_topic": "...",
//     "human_review": "...",
//     "ai_reviewer_1": "...",
//     "ai_reviewer_2": "...",
//     "ai_reviewer_3": "...",
//     "hypothesis_development": "..."
//   },
//   "forum_id_2": { ... }
// }

(function() {
    // 数据结构：forum_id 作为 key，包含所有表格信息
    // Data structure: forum_id as key, containing all table information
    const tableData = {};
    
    // 查找所有包含 openreview 链接的行
    // Find all rows containing openreview links
    const links = Array.from(document.querySelectorAll('a[href*="openreview.net/forum"]'));
    
    links.forEach(link => {
        const match = link.href.match(/forum\?id=([^&]+)/);
        if (!match) return;
        
        const forumId = match[1];
        const row = link.closest('tr');
        
        if (!row) return;
        
        // 提取表格数据
        // Extract table data
        const cells = Array.from(row.querySelectorAll('td'));
        
        if (cells.length < 7) return; // 确保有足够的列 / Ensure enough columns
        
        // 提取各个字段
        // Extract each field
        const title = link.textContent.trim();
        
        // Status (通常在第二个单元格)
        // Status (usually in second cell)
        const statusCell = cells[1];
        const status = statusCell ? statusCell.textContent.trim() : '';
        
        // Primary Topic (通常在第三个单元格)
        // Primary Topic (usually in third cell)
        const primaryTopicCell = cells[2];
        const primaryTopic = primaryTopicCell ? primaryTopicCell.textContent.trim() : '';
        
        // Secondary Topic (通常在第四个单元格)
        // Secondary Topic (usually in fourth cell)
        const secondaryTopicCell = cells[3];
        const secondaryTopic = secondaryTopicCell ? secondaryTopicCell.textContent.trim() : '';
        
        // Human Review (通常在第五个单元格)
        // Human Review (usually in fifth cell)
        const humanReviewCell = cells[4];
        const humanReview = humanReviewCell ? humanReviewCell.textContent.trim() : '';
        
        // AI Reviewer 1, 2, 3 (通常在第六、七、八个单元格)
        // AI Reviewer 1, 2, 3 (usually in sixth, seventh, eighth cells)
        const aiReviewer1 = cells[5] ? cells[5].textContent.trim() : '';
        const aiReviewer2 = cells[6] ? cells[6].textContent.trim() : '';
        const aiReviewer3 = cells[7] ? cells[7].textContent.trim() : '';
        
        // Hypothesis Development (通常在最后一个单元格)
        // Hypothesis Development (usually in last cell)
        const hypothesisCell = cells[cells.length - 1];
        const hypothesisDevelopment = hypothesisCell ? hypothesisCell.textContent.trim() : '';
        
        // 以 forum_id 为 key，存储所有表格信息
        // Store all table information with forum_id as key
        tableData[forumId] = {
            title: title,
            status: status,
            primary_topic: primaryTopic,
            secondary_topic: secondaryTopic,
            human_review: humanReview,
            ai_reviewer_1: aiReviewer1,
            ai_reviewer_2: aiReviewer2,
            ai_reviewer_3: aiReviewer3,
            hypothesis_development: hypothesisDevelopment
        };
    });
    
    // 复制到剪贴板
    // Copy to clipboard
    const jsonText = JSON.stringify(tableData, null, 2);
    navigator.clipboard.writeText(jsonText).then(() => {
        console.log(`✅ 已提取 ${Object.keys(tableData).length} 个 forum ID 及其表格数据并复制到剪贴板`);
        console.log(`✅ Extracted ${Object.keys(tableData).length} forum IDs and their table data, copied to clipboard`);
        console.log('📋 请将内容保存到 downloads/table_data.json 文件中');
        console.log('📋 Please save the content to downloads/table_data.json file');
        console.log('\n格式说明 / Format: {forum_id: {title, status, primary_topic, ...}}');
        console.log('Format: {forum_id: {title, status, primary_topic, ...}}');
    }).catch(err => {
        console.log('⚠️  无法复制到剪贴板，请手动复制下面的内容');
        console.log('⚠️  Cannot copy to clipboard, please manually copy the content below:');
        console.log('\n' + jsonText);
    });
    
    // 也输出到控制台
    // Also output to console
    console.log('\n表格数据（forum_id 和对应信息）/ Table data (forum_id and corresponding info):');
    console.log(tableData);
    
    return tableData;
})();

