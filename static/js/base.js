function showe(e){
	var be="b"+e
	var sidebar_list = ["index","install","conf","bmonitor","tool","task","set"]
	for (var i = 0; i < sidebar_list.length; i ++){ 
		document.getElementById(sidebar_list[i]).style.display="none"
		document.getElementById("b"+sidebar_list[i]).style.backgroundColor="#111"
		document.getElementById("b"+sidebar_list[i]).style.color='grey'
	}
	document.getElementById(e).style.display=""
	document.getElementById(be).style.backgroundColor="#0066FF"
	document.getElementById(be).style.color='white'

}
