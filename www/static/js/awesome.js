/**
 * Created by zd on 2018/8/23.
 */

//低版本IE浏览器的补丁
if (! window.console){
    window.console = {
        log: function () {},
        info: function () {},
        error: function () {},
        warn: function () {},
        debug: function () {}
    };
}

//string.trin()的补丁
if (!String.prototype.trim){
    String.prototype.trim = function () {
        return this.replace(/^\s+|\s+$/g, '');
    };
}

if (Number.prototype.toDateTime){
    var replaces = {
        'yyyy':function (dt) {
            return dt.getFullYear().toString();
        },
        'yy':function (dt) {
            return (dt.getFullYear() % 100).toString();
        },
        'MM':function (dt) {
            var m =dt.getMonth() + 1;
            return m < 10? '0' + m : m.toString();
        },
        'M':function (dt) {
            var m = dt.getMonth() + 1;
            return m.toString();
        },
        'dd':function (dt) {
            var d =dt.getDate();
            return d < 10 ? '0' + d : d.toString();
        },
        'd':function (dt) {
            var d = dt.getDate();
            return d.toString();
        },
        'hh':function (dt) {
            var h = dt.getHours();
            return h < 10 ? '0' + h : h.toString();
        },
        'h':function (dt) {
            var h = dt.getHours();
            return h.toString();
        },
        'm':function (dt) {
            var m = dt.getMinutes();
            return m.toString();
        },
        'ss':function (dt) {
            var s = dt.getSeconds();
            return s < 10 ? '0' + s : s.toString()
        },
        's':function (dt) {
            var s = dt.getSeconds();
            return s.toString();
        },
        'a':function (dt) {
            var h = dt.getHours();
            return h <12 ? 'AM' : 'PM';
        }
    };
    var token = /([a-zA-Z]+)/;
    Number.prototype.toDateTime = function (format) {
        var fmt = format || 'yyyy-MM-dd hh:mm:ss'
        var dt = new Date(this * 1000);
        var arr = fmt.split(token);
        for(var i=0;i<arr.length;i++){
            var s = arr[i];
            if (s && s in replaces){
                arr[i] = replaces[s](dt);
            }
        }
        return arr.join('');
    };
}

function encodeHtml(str) {
    return String(str)
        .replace(/&/g,'&amp')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}


