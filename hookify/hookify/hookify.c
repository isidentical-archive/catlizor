#include <Python.h>
#include <sys/mman.h>

#pragma pack(push, 1)
    static struct { 
        char push_rax; 
        char mov_rax[2];
        char addr[8];
        char jmp_rax[2]; 
    } 

    jumper = {
        .push_rax = 0x50,
        .mov_rax  = {0x48, 0xb8},
        .jmp_rax  = {0xff, 0xe0}
    };
#pragma pack(pop)

extern PyObject* _PyFunction_FastCallKeywords(PyObject *func, PyObject *const *stack, Py_ssize_t nargs, PyObject *kwnames);


static int unprotect_page(void* addr) {
    return mprotect((char *)((size_t)addr & ~(sysconf(_SC_PAGE_SIZE) -1)), sysconf(_SC_PAGE_SIZE), PROT_READ | PROT_WRITE | PROT_EXEC);
}

int hookifier(void* target, void* replace) {
    /* Some parts based on libhook */
    int count;

    if(unprotect_page(replace) || unprotect_page(target)) {
        return 1;
    }

    for(count = 0; count < 255 && ((unsigned char*)replace)[count] != 0x90; ++count);

    if(count == 255) {
        return 1;
    }
    
    memmove(replace+1, replace, count);
    *((unsigned char *)replace) = 0x58;
    memcpy(jumper.addr, &replace, sizeof (void *));
    memcpy(target, &jumper, sizeof jumper);

    return 0;
}

PyObject *
hookify_PyFunction_FastCallKeywords(PyObject *func, PyObject *const *stack,
                             Py_ssize_t nargs, PyObject *kwnames)
{
    __asm__("NOP");
    PyCodeObject *co = (PyCodeObject *)PyFunction_GET_CODE(func);
    PyObject *globals = PyFunction_GET_GLOBALS(func);
    PyObject *argdefs = PyFunction_GET_DEFAULTS(func);
    PyObject *kwdefs, *closure, *name, *qualname;
    PyObject **d;
    Py_ssize_t nkwargs = (kwnames == NULL) ? 0 : PyTuple_GET_SIZE(kwnames);
    Py_ssize_t nd;
    PyObject *module, *catlizor, *catlizor_fnmap, *catlizor_instance;
    int catalized = 0;
    assert(PyFunction_Check(func));
    assert(nargs >= 0);
    assert(kwnames == NULL || PyTuple_CheckExact(kwnames));
    assert((nargs == 0 && nkwargs == 0) || stack != NULL);

    kwdefs = PyFunction_GET_KW_DEFAULTS(func);
    closure = PyFunction_GET_CLOSURE(func);
    name = ((PyFunctionObject *)func) -> func_name;
    qualname = ((PyFunctionObject *)func) -> func_qualname;

    if (argdefs != NULL) {
        d = &PyTuple_GET_ITEM(argdefs, 0);
        nd = PyTuple_GET_SIZE(argdefs);
    }
    else {
        d = NULL;
        nd = 0;
    }
    module = PyImport_AddModule("__main__");
    
    if (PyObject_HasAttrString(module, "Catlizor")){
        catlizor = PyObject_GetAttrString(module, "Catlizor");
        catlizor_fnmap = PyObject_GetAttrString(catlizor, "FN_MAP");
        if (PyDict_Contains(catlizor_fnmap, func)){
            catlizor_instance = PyDict_GetItemWithError(catlizor_fnmap, func);
            catalized = 2;
        }
        Py_DECREF(catlizor);
        Py_DECREF(catlizor_fnmap);
    }
    
    if (catlizor_instance != NULL && catalized == 2){
        if (PyObject_HasAttrString(catlizor_instance, "exc_capi")){
            PyObject_CallMethod(catlizor_instance, "exc_capi", "(iO)", -1, func);
        }
    }
    PyObject *result = _PyEval_EvalCodeWithName((PyObject*)co, globals, (PyObject *)NULL,
                                    stack, nargs,
                                    nkwargs ? &PyTuple_GET_ITEM(kwnames, 0) : NULL,
                                    stack + nargs,
                                    nkwargs, 1,
                                    d, (int)nd, kwdefs,
                                    closure, name, qualname);

    if (catlizor_instance != NULL && catalized == 2){
        if (PyObject_HasAttrString(catlizor_instance, "exc_capi")){
            PyObject_CallMethod(catlizor_instance, "exc_capi", "(iOO)", 0, func, result);
        }
    }
    if (catlizor_instance != NULL && catalized == 2){
        if (PyObject_HasAttrString(catlizor_instance, "exc_capi")){
            PyObject_CallMethod(catlizor_instance, "exc_capi", "(iO)", 1, func);
        }
    }
    return result;
}

static PyMethodDef module_methods[] = {
    {NULL}
};


static struct PyModuleDef hookify =
{
    PyModuleDef_HEAD_INIT,
    "hookify",
    NULL,
    -1, 
    module_methods
};

PyMODINIT_FUNC PyInit_hookify(void) {
    __asm__("");
    hookifier(_PyFunction_FastCallKeywords, &hookify_PyFunction_FastCallKeywords);
    return PyModule_Create(&hookify);
}

