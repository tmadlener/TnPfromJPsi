// general header containing some (copy & pasted from other repos) functionality

#ifndef TNP_JPSI_GENERALHELPER_H__
#define TNP_JPSI_GENERALHELPER_H__

#include "TObject.h"
#include "TDirectory.h"
#include "TIterator.h"
#include "TKey.h"
#include "TClass.h"

#include <functional>
#include <vector>
#include <string>
#include <sstream>

/** check if the object is of type RT via TObject::InheritsFrom()*/
template<typename RT> inline
bool inheritsFrom(const TObject* obj)
{
  // it seems the call to ::IsA() is not necessary (This might has to be revisited for versions below 6).
  // it is even no longer listed in the documentation for version 6.07/07 (17.08.16). Nevertheless it still compiles
  return obj/*->IsA()*/->InheritsFrom(RT::Class());
}

/**
 * replace all instances of tar in str by rep.
 * Returns the number of replacements that took place if succesful or -2 if the tar is empty or -1 if str is empty.
 */
int replace(std::string& str, const std::string& tar, const std::string& rep)
{
  // handle some trivial "error" cases that make no sense in usage
  if (tar.empty()) return -2;
  if (str.empty()) return -1;

  const size_t tarlen = tar.length();
  const size_t replen = rep.length();
  if (tarlen > str.length()) return 0; // we can't replace something that doesn't even fit

  int repCtr = 0;

  size_t pos = 0;
    while ((pos = str.find(tar,pos)) != std::string::npos) {
    str.replace(pos, replen, rep);
    pos += replen;
    repCtr++;
  }

  return repCtr;
}

/** split string at delimiter delim and return vector of all substrings. If a token is empty it will be ignored. */
std::vector<std::string> splitString(const std::string& in, const char delim)
{
  std::vector<std::string> tokens;
  std::stringstream sstr(in);
  std::string tok;
  while(std::getline(sstr,tok,delim)) {
    if(!tok.empty()) {
      tokens.push_back(tok);
    }
  }

  return tokens;
}

/**
 * No-op function taking a TDirectory* that is used as default argument for the dirFunc in
 * recurseOnFile below.
 */
std::function<void(TDirectory*)> noopVoidFunction([](TDirectory*)->void {;});

/**
 * Generic root file recursion function that traverses all TDirectories that can be found in a TFile.
 * For every key that is found in the file it is checked if it inherits from TDirectory and if not
 * the function passed in via the func parameter is executed.
 *
 * The definition of the default argument of dirFunc makes it possible to invoke this function with
 * only two arguments when no additional action on a directory is needed.
 *
 * @param file the TFile or TDirectory to recurse on.
 * @param func any function object that takes a TObject* as its single argument. NOTE: This is a reference!
 * This is by choice, as in this way a functor can be passed in, which can then be accessed by e.g. the dirFunc
 * to set something directory specific.
 * @param dirFunc any function taking a TDirectory* as its single argument that is executed on each
 * directory but is not part of the recursion.
 */
template<typename T, typename F, typename DF = decltype(noopVoidFunction)>
void recurseOnFile(const T* file, F& func, DF dirFunc = noopVoidFunction)
{
  TIter nextKey(file->GetListOfKeys());
  TKey* key = nullptr;
  while ((key = static_cast<TKey*>(nextKey()))) {
    TObject* obj = key->ReadObj();
    if (!inheritsFrom<TDirectory>(obj)) {
      func(obj);
    } else {
      // TDirectory is the base-class that implements the GetListOfKeys function
      // static_cast should be fine here, since we already checked above if we inherit from TDirectory
      TDirectory* dir = static_cast<TDirectory*>(obj);
      dirFunc(dir);
      recurseOnFile(dir, func, dirFunc);
    }
  }
}

#endif
