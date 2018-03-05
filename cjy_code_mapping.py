err_code_map = {
    -1001: '用户参数异常',
    -1002: '无此用户名',
    -1003: '用户名的密码出错',
    -10031: '用户状态异常',
    -1004: '类型参数错误',
    -1005: '无可用题分',
    -10061: '不是有效的图片文件',
    -100612: 'base64字符解析异常',
    -10062: '文件超大 1024k',
    -10064: '图片无法被识别',
    -10071: '软件上传图片异常',
    -2001: '上传图片出错',
    -2003: '存储图片时出现异常',
    -3001: '系统超时',
    -3002: '系统超时',
    -1011: '报错调用异常',
    -1013: '软件报错异常',
    -1021: '用户名的组成只能是字母和数字',
    -1022: '用户名的字符长应该界于6至16之间',
    -1023: '密码的字符长应该界于6至20之间',
    -1024: '账号不能重复注册',
    -1032: '用户名和充值卡不能为空',
    -1033: '无此充值卡号',
    -1034: '充值卡已被使用'
}

err_type_map = {
    'repeat': [-10061, -100612, -10062, -10064, -3001, -3002],
    'error': [-1001, -1002, -1003, -10031, -1004, -1005, -10071, -2001, -2003, -1011,
              -1013, -1021, -1022, -1023, -1024, -1032, -1033, -1034]
}