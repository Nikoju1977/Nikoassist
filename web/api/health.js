'use strict';
module.exports=(req,res)=>{
 res.setHeader('Cache-Control','no-store');
 if(req.method!=='GET')return res.status(405).json({ok:false});
 return res.status(200).json({ok:true,service:'nikoassist-web',version:'1.0',mode:'public-tools',pythonEngineConnected:false, checkedAt:new Date().toISOString()});
};